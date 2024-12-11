# backend/agents/recommendation_agent.py
from typing import Dict, Callable, List
from prompts.prompt_template import recommendation_template
from datetime import datetime
import json
import asyncio

class RecommendationAgent:
    def __init__(self, llm):
        """Initialize the recommendation agent with LLM instance"""
        self.llm = llm
        self._status_callback = None
        self.timeout = 90  # 90 seconds timeout

    def set_status_callback(self, callback: Callable):
        """Set callback for status updates"""
        self._status_callback = callback

    async def _update_status(self, message: str, progress: float):
        """Send status update through callback if set"""
        if self._status_callback:
            await self._status_callback(message, progress)

    def _format_alumni_results(self, alumni_profiles: Dict, queries: List) -> str:
        """Format alumni search results with their corresponding queries"""
        formatted_results = []
        for query, results in zip(queries, alumni_profiles.values()):
            formatted_results.append(f"Query: {query}")
            for result in results:
                formatted_results.append(f"  - {result}")
        return "\n".join(formatted_results)

    def _format_internet_results(self, internet_results: Dict, queries: List) -> str:
        """Format internet insights with their corresponding queries"""
        formatted_results = []
        for query, result in zip(queries, internet_results.values()):
            formatted_results.append(f"Query: {query}\nResult: {result}")
        return "\n\n".join(formatted_results)

    async def generate_recommendations(self, search_results: Dict, student_summary: str) -> Dict:
        """Generate recommendations based on search results and student profile"""
        try:
            await self._update_status("Formatting results for analysis...", 0.3)
            
            # Extract and format results with queries
            alumni_queries = search_results["queries"]["database_queries"]
            internet_queries = search_results["queries"]["internet_queries"]
            alumni_results = self._format_alumni_results(search_results["results"]["alumni_profiles"], alumni_queries)
            internet_results = self._format_internet_results(search_results["results"]["internet_insights"], internet_queries)
            
            # Generate recommendations using LLM
            await self._update_status("Generating recommendations...", 0.4)
            recommendation_prompt = recommendation_template.format(
                context=student_summary,
                alumni_profiles=alumni_results,
                internet_insights=internet_results
            )
            
            # Debug: Log the prompt size
            print("\n--- PROMPT DEBUGGING ---")
            print(f"Prompt size (characters): {len(recommendation_prompt)}")
            print("First 500 characters of the prompt:")
            print(recommendation_prompt[:500])
            
            try:
                # Increase timeout temporarily to debug
                debug_timeout = 180  # 3 minutes
                print(f"Calling LLM with timeout: {debug_timeout} seconds")
                
                start_time = datetime.utcnow()
                response = await asyncio.wait_for(
                    self.llm.acomplete(recommendation_prompt),
                    timeout=debug_timeout
                )
                end_time = datetime.utcnow()
                print(f"LLM response received in {(end_time - start_time).total_seconds()} seconds")
                
                await self._update_status("Processing LLM response...", 0.8)
                
                # Parse the LLM response immediately into a Python dictionary
                try:
                    recommendations_dict = json.loads(response.text.strip())
                except json.JSONDecodeError as json_err:
                    print(f"Error parsing LLM response as JSON: {str(json_err)}")
                    print(f"Raw LLM response: {response.text.strip()}")
                    raise ValueError(f"Invalid JSON in LLM response: {str(json_err)}")
                
                # Validate the structure contains the recommendations key
                if "recommendations" not in recommendations_dict:
                    raise ValueError("LLM response missing 'recommendations' key")
                
                await self._update_status("Finalizing recommendations...", 0.9)
                
                # Return structured response with parsed recommendations
                return {
                    "status": "success",
                    "timestamp": datetime.utcnow().isoformat(),
                    "student_summary": student_summary,
                    "recommendations": recommendations_dict["recommendations"],
                    "metadata": {
                        "queries": search_results["queries"],
                        "sources": {
                            "alumni_count": sum(len(v) for v in search_results["results"]["alumni_profiles"].values()),
                            "internet_count": len(search_results["results"]["internet_insights"])
                        }
                    }
                }

            except asyncio.TimeoutError:
                await self._update_status("Recommendation generation timed out", 1.0)
                print("Timeout occurred: LLM did not respond in time.")
                return {
                    "status": "error",
                    "error": "Recommendation generation timed out",
                    "timestamp": datetime.utcnow().isoformat()
                }

        except Exception as e:
            error_message = str(e)
            print(f"Error generating recommendations: {error_message}")
            await self._update_status(f"Error: {error_message}", 1.0)
            return {
                "status": "error",
                "error": error_message,
                "timestamp": datetime.utcnow().isoformat()
            }

