# backend/agents/recommendation_agent.py
from typing import Dict, List
from prompts.prompt_template import recommendation_template
from pydantic import BaseModel
from datetime import datetime

class RecommendationAgent:
    def __init__(self, llm):
        """Initialize the recommendation agent with LLM instance"""
        self.llm = llm

    def _structure_search_results(self, search_results: Dict) -> Dict:
        """Structure search results for recommendation generation"""
        return {
            "alumni_profiles": search_results["results"]["alumni_profiles"],
            "internet_insights": search_results["results"]["internet_insights"]
        }

    def _format_alumni_results(self, alumni_profiles: Dict) -> str:
        """Format alumni search results for prompt input"""
        formatted_results = []
        for query, results in alumni_profiles.items():
            formatted_results.append(f"Query: {query}")
            for i, result in enumerate(results, 1):
                formatted_results.append(f"Result {i}: {result}")
        return "\n\n".join(formatted_results)

    def _format_internet_results(self, internet_insights: Dict) -> str:
        """Format internet search results for prompt input"""
        formatted_results = []
        for question, answer in internet_insights.items():
            formatted_results.append(f"Question: {question}\nAnswer: {answer}")
        return "\n\n".join(formatted_results)

    async def generate_recommendations(self, search_results: Dict, student_summary: str) -> Dict:
        """Generate recommendations based on search results and student profile"""
        try:
            # Structure search results
            combined_responses = self._structure_search_results(search_results)
            
            # Format results for prompt
            formatted_alumni = self._format_alumni_results(combined_responses["alumni_profiles"])
            formatted_internet = self._format_internet_results(combined_responses["internet_insights"])

            # Generate recommendations using LLM
            recommendation_prompt = recommendation_template.format(
                context=student_summary,
                alumni_profiles=formatted_alumni,
                internet_insights=formatted_internet
            )

            response = await self.llm.acomplete(recommendation_prompt)
            recommendations = response.text.strip()

            # Return structured response
            return {
                "status": "success",
                "timestamp": datetime.utcnow().isoformat(),
                "student_summary": student_summary,
                "recommendations": recommendations,
                "metadata": {
                    "queries": search_results["queries"],
                    "sources": {
                        "alumni_count": len(combined_responses["alumni_profiles"]),
                        "internet_count": len(combined_responses["internet_insights"])
                    }
                }
            }

        except Exception as e:
            print(f"Error generating recommendations: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
