# search_agent.py
from typing import Dict, List, Tuple
from llama_index.core.schema import NodeWithScore
import asyncio
from llama_index.core.workflow import Workflow, step, Context, Event, StartEvent, StopEvent
from llama_index.core import VectorStoreIndex
from tavily import TavilyClient
from prompts.prompt_template import query_diversification_template, internet_search_template

class SearchStatus(Event):
    """Event for tracking search progress"""
    phase: str
    message: str
    progress: float  # 0 to 1

class DatabaseSearchWorkflow(Workflow):
    """Workflow for database search using LlamaIndex pattern"""
    
    def __init__(self, hybrid_index: VectorStoreIndex = None, timeout: int = 60, verbose: bool = True):
        super().__init__(timeout=timeout, verbose=verbose)
        self.hybrid_index = hybrid_index

    @step
    async def start(self, ctx: Context, ev: StartEvent) -> StopEvent:
        """Main workflow step following LlamaIndex pattern"""
        queries = ev.get("search_query")
        if not queries or not self.hybrid_index:
            return StopEvent({"error": "Missing queries or index", "results": {}})

        try:
            # Setup retrievers
            vector_retriever = self.hybrid_index.as_retriever(
                vector_store_query_mode="default",
                similarity_top_k=5
            )
            text_retriever = self.hybrid_index.as_retriever(
                vector_store_query_mode="sparse",
                similarity_top_k=5
            )

            # Run both retrievers for each query
            results = {}
            for query in queries:
                query_results = []
                for retriever in [vector_retriever, text_retriever]:
                    retrieved = await retriever.aretrieve(query)
                    query_results.extend(retrieved)
                
                # Sort by score and take top 5
                sorted_results = sorted(query_results, key=lambda x: x.score or 0.0, reverse=True)
                results[query] = "\n".join([
                    node.node.get_content()
                    for node in sorted_results[:5]
                    if node.node is not None
                ])

            return StopEvent(results)

        except Exception as e:
            print(f"Database search error: {str(e)}")
            return StopEvent({"error": str(e), "results": {}})

class InternetSearchWorkflow(Workflow):
    """Workflow for internet search"""
    def __init__(self, tavily=None, timeout: int = 60, verbose: bool = True):
        super().__init__(timeout=timeout, verbose=verbose)
        self.tavily = tavily

    @step
    async def start(self, ctx: Context, ev: StartEvent) -> StopEvent:
        search_questions = ev.get("search_questions")
        if not search_questions:
            return StopEvent({"error": "No search questions provided"})

        try:
            results = {}
            for i, question in enumerate(search_questions):
                print("--------------------------------")
                print(f"Searching for question {i+1}: {question}")
                await asyncio.sleep(0.5 * i)  # Stagger requests
                try:
                    answer = await asyncio.wait_for(
                        asyncio.to_thread(
                            self.tavily.qna_search,
                            query=question,
                            search_depth="advanced",
                            topic="general",
                            max_results=10
                        ),
                        timeout=55
                    )
                    if answer:
                        results[question] = answer
                except Exception as e:
                    print(f"Error in Tavily search for query '{question}': {str(e)}")
                    continue

            return StopEvent(results)
        except Exception as e:
            print(f"Internet search error: {str(e)}")
            return StopEvent({"error": str(e)})
class SearchAgent:
    def __init__(self, llm, hybrid_index: VectorStoreIndex, tavily_client: TavilyClient):
        self.llm = llm
        self.hybrid_index = hybrid_index
        self.tavily_client = tavily_client
        self._status_callback = None
    def set_status_callback(self, callback):
        """Set callback for status updates"""
        self._status_callback = callback

    async def _update_status(self, phase: str, message: str, progress: float):
        """Update search status"""
        if self._status_callback:
            await self._status_callback(SearchStatus(phase=phase, message=message, progress=progress))

    async def generate_search_queries(self, summary: str) -> Tuple[List[str], List[str]]:
        """Generate database and internet search queries based on the summary."""
        try:
            print("Generating search queries from summary:", summary)

            # Generate database queries
            db_response = await self.llm.acomplete(
                prompt=query_diversification_template.format(summary=summary)
            )
            db_response_text = db_response.text.strip()
            raw_queries = [q.strip() for q in db_response_text.split("\n\n")]
            db_queries = [
                query.replace('\n', ' ').strip().strip('"')
                for query in raw_queries 
                if query.strip()
            ]

            # Generate internet queries
            internet_response = await self.llm.acomplete(
                prompt=internet_search_template.format(context=summary)
            )
            internet_queries = [
                query.strip().strip('"') 
                for query in internet_response.text.strip().split("\n\n") 
                if query.strip()
            ]

            print("Database queries generated:", db_queries)
            print("Internet queries generated:", internet_queries)

            return db_queries, internet_queries
        except Exception as e:
            print(f"Error generating queries: {e}")
            raise

    async def execute_combined_search(self, summary: str) -> Dict:
        """Execute both database and internet searches in parallel."""
        try:
            await self._update_status("init", "Starting search process...", 0.1)
            await self._update_status("query_generation", "Generating search queries...", 0.2)
            db_queries, internet_queries = await self.generate_search_queries(summary)

            await self._update_status("search", "Running parallel searches...", 0.4)
            db_workflow = DatabaseSearchWorkflow(hybrid_index=self.hybrid_index, timeout=60, verbose=True)
            internet_workflow = InternetSearchWorkflow(tavily=self.tavily_client, timeout=60, verbose=True)

            # Run workflows
            await self._update_status("search_db", "Searching alumni database...", 0.6)
            db_results = await db_workflow.run(search_query=db_queries)
            await self._update_status("search_internet", "Searching internet resources...", 0.8)
            internet_results = await internet_workflow.run(search_questions=internet_queries)
            await self._update_status("complete", "Search completed", 1.0)
            return {
                "queries": {
                    "database_queries": db_queries,
                    "internet_queries": internet_queries
                },
                "results": {
                    "alumni_profiles": db_results,
                    "internet_insights": internet_results
                }
            }

        except Exception as e:
            await self._update_status("error", f"Search failed: {str(e)}", 1.0)
            print(f"Search error: {str(e)}")
            raise