# backend/agents/search_agent.py
from typing import Dict, List, Tuple
from llama_index.core.schema import NodeWithScore
import asyncio
from llama_index.core.workflow import Workflow, step, Context, Event, StartEvent, StopEvent
from llama_index.core import VectorStoreIndex
from tavily import TavilyClient
from prompts.prompt_template import query_diversification_template, internet_search_template

class DatabaseSearchResultsEvent(Event):
    """Event containing database search results."""
    fusion_results_dict: Dict[str, List[NodeWithScore]]

class QuestionsGeneratedEvent(Event):
    """Event containing generated internet context search questions."""
    internet_search_questions: List[str]

class SearchAgent:
    def __init__(self, llm, hybrid_index: VectorStoreIndex, tavily_client: TavilyClient):
        self.llm = llm
        self.hybrid_index = hybrid_index
        self.tavily_client = tavily_client

    async def generate_search_queries(self, summary: str) -> tuple[List[str], List[str]]:
        """Generate both database and internet search queries from profile summary"""
        # Generate database queries
        db_response = await self.llm.acomplete(
            query_diversification_template.format(summary=summary)
        )
        db_queries = [q.strip() for q in db_response.text.strip().split('\n') if q.strip()]

        # Generate internet queries
        internet_response = await self.llm.acomplete(
            internet_search_template.format(context=summary)
        )
        internet_queries = [part.strip('"') for part in internet_response.text.strip().split('\n\n')]

        return db_queries, internet_queries

    class DatabaseSearchWorkflow(Workflow):
        async def run_queries(self, queries: List[str], retrievers: List) -> Dict[Tuple[str, int], List[NodeWithScore]]:
            async def _retrieve(query: str, retriever, idx: int):
                result = await retriever.aretrieve(query)
                return (query, idx), result

            tasks = [
                _retrieve(query, retriever, idx)
                for query in queries
                for idx, retriever in enumerate(retrievers)
            ]

            results = await asyncio.gather(*tasks)
            return dict(results)

        async def fuse_results_per_query(
            self, 
            results_dict: Dict[Tuple[str, int], List[NodeWithScore]], 
            similarity_top_k: int = 5
        ) -> Dict[str, List[NodeWithScore]]:
            k = 60.0
            query_fusion_results = {}

            # Group results by query
            query_groups = {}
            for (query, _), nodes_with_scores in results_dict.items():
                if query not in query_groups:
                    query_groups[query] = []
                query_groups[query].extend(nodes_with_scores)

            # Fuse results for each query
            for query, nodes_with_scores in query_groups.items():
                fused_scores = {}
                text_to_node = {}

                # Calculate reciprocal rank fusion scores
                for rank, node_with_score in enumerate(
                    sorted(nodes_with_scores, key=lambda x: x.score or 0.0, reverse=True)
                ):
                    text = node_with_score.node.get_content()
                    text_to_node[text] = node_with_score
                    if text not in fused_scores:
                        fused_scores[text] = 0.0
                    fused_scores[text] += 1.0 / (rank + k)

                # Sort by fusion scores
                reranked_results = dict(
                    sorted(fused_scores.items(), key=lambda x: x[1], reverse=True)
                )

                # Create final reranked list
                reranked_nodes = []
                for text, score in reranked_results.items():
                    reranked_nodes.append(text_to_node[text])
                    reranked_nodes[-1].score = score

                query_fusion_results[query] = reranked_nodes[:similarity_top_k]

            return query_fusion_results

        @step
        async def perform_searches(self, ctx: Context, ev: StartEvent) -> StopEvent:
            queries = ev.get("search_query")
            hybrid_index = ctx.get("hybrid_index")

            # Setup retrievers with fixed top_k
            vector_retriever = hybrid_index.as_retriever(
                vector_store_query_mode="default",
                similarity_top_k=5
            )
            text_retriever = hybrid_index.as_retriever(
                vector_store_query_mode="sparse",
                similarity_top_k=5
            )

            # Run searches
            raw_results_dict = await self.run_queries(queries, [vector_retriever, text_retriever])
            
            # Fuse results
            fusion_results_dict = await self.fuse_results_per_query(
                raw_results_dict, 
                similarity_top_k=5
            )
            # format the results
            formatted_results = {
                query: [node.node.get_content() for node in nodes] 
                for query, nodes in fusion_results_dict.items()
            }

            return StopEvent(formatted_results)

    class InternetSearchWorkflow(Workflow):
        def __init__(self, timeout: int = 60, verbose: bool = True, tavily=None):
            super().__init__(timeout=timeout, verbose=verbose)
            self.tavily = tavily

        @step
        async def perform_internet_searches(self, ctx: Context, ev: StartEvent) -> StopEvent:
            search_questions = ev.get("search_questions")

            async def search_question(question, delay_seconds: float = 0.5):
                try:
                    await asyncio.sleep(delay_seconds)
                    context = await asyncio.get_event_loop().run_in_executor(
                        None,
                        lambda: self.tavily.qna_search(
                            query=question,
                            search_depth="advanced",
                            topic="general",
                            days=365,
                            max_results=6
                        )
                    )
                    return {"question": question, "answer": context} if context else None
                except Exception as e:
                    print(f"Failed to perform Tavily QnA search for query: {question}")
                    print(f"Error: {str(e)}")
                    return None

            all_results = [
                result for result in
                await asyncio.gather(*[
                    search_question(q, delay_seconds=i * 0.5)
                    for i, q in enumerate(search_questions)
                ])
                if result is not None
            ]

            # Convert the list of results into a dictionary
            results_dict = {res['question']: res['answer'] for res in all_results}
            return StopEvent(results_dict)

    async def execute_combined_search(self, summary: str) -> Dict:
        """Execute both database and internet searches in parallel"""
        try:
            # Generate both types of queries
            db_queries, internet_queries = await self.generate_search_queries(summary)

            # Execute both searches in parallel
            db_workflow = self.DatabaseSearchWorkflow(timeout=120)
            db_workflow.hybrid_index = self.hybrid_index
            db_search_task = asyncio.create_task(
                db_workflow.run(search_query=db_queries)
            )

            internet_workflow = self.InternetSearchWorkflow(
                timeout=60, 
                tavily=self.tavily_client
            )
            internet_search_task = asyncio.create_task(
                internet_workflow.run(search_questions=internet_queries)
            )

            # Wait for both searches to complete
            db_results, internet_results = await asyncio.gather(
                db_search_task, 
                internet_search_task
            )

            # Return combined results with queries for storage
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
            print(f"Search error: {str(e)}")
            raise