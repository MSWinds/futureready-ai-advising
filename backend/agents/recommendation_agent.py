# backend/agents/recommendation_agent.py
from typing import Dict, Callable, List
from pydantic import BaseModel, Field, ConfigDict
from prompts.prompt_template import recommendation_template
from datetime import datetime
import asyncio

# Pydantic models for structured output
class QuickView(BaseModel):
    title: str = Field(
        ..., 
        description="A short, clear, and specific name for the academic pathway (e.g., 'AI Research Path')."
    )
    summary: str = Field(
        ..., 
        description="A concise 2-3 sentence summary explaining how the pathway aligns with the student's profile and career goals."
    )
    keyPoints: List[str] = Field(
        ..., 
        description="Exactly three critical considerations that make this pathway relevant for the student (e.g., 'Strong alignment with research interests', 'Potential for publishing AI research')."
    )
    nextStep: str = Field(
        ..., 
        description="A specific and actionable next step for the advisor to discuss with the student (e.g., 'Introduce the student to Dr. John Doe for a mentorship discussion')."
    )

    model_config = ConfigDict(extra="forbid")

class DetailedView(BaseModel):
    reasoning: str = Field(
        ..., 
        description="An in-depth explanation of why this pathway is a good fit for the student, considering their background, goals, and strengths."
    )
    evidence: Dict[str, str] = Field(
        ..., 
        description="Supporting evidence that includes alumni patterns (examples of alumni who followed similar paths) and industry context (relevant trends or insights that validate the pathway)."
    )
    discussionPoints: List[str] = Field(
        ..., 
        description="Exactly three actionable discussion points for advisors to explore with the student (e.g., 'Explore relevant universities for AI research', 'Discuss opportunities for publishing research')."
    )

    model_config = ConfigDict(extra="forbid")

class Recommendation(BaseModel):
    id: int = Field(
        ..., 
        description="A unique identifier for the recommendation, starting at 1 and incrementing for each suggestion."
    )
    type: str = Field(
        ..., 
        description="The category of the recommendation: 'alumni' for alumni-based pathways, 'trend' for emerging industry trends, or 'figure' for notable figure-inspired pathways."
    )
    quickView: QuickView = Field(
        ..., 
        description="The high-level summary of the recommendation, designed for quick reference."
    )
    detailedView: DetailedView = Field(
        ..., 
        description="A detailed breakdown of the recommendation, including reasoning, evidence, and actionable discussion points."
    )

    model_config = ConfigDict(extra="forbid")

class RecommendationsResponse(BaseModel):
    recommendations: List[Recommendation] = Field(
        ..., 
        description="A list of exactly 5 pathway recommendations, including 3 based on alumni, 1 on an emerging trend, and 1 inspired by a notable figure."
    )

    model_config = ConfigDict(extra="forbid")



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

    def _prepare_json_schema(self):
        """Generate a valid OpenAI-compatible JSON schema"""
        raw_schema = RecommendationsResponse.model_json_schema()
        raw_schema["required"] = list(raw_schema["properties"].keys())

        # Recursively ensure additionalProperties is False
        def set_additional_properties_false(schema_part):
            if isinstance(schema_part, dict):
                if "properties" in schema_part:
                    schema_part["additionalProperties"] = False
                for value in schema_part.values():
                    set_additional_properties_false(value)

        set_additional_properties_false(raw_schema)
        return {
            "name": "recommendations_response",
            "schema": raw_schema
        }

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

            schema = self._prepare_json_schema()

            try:
                response = await asyncio.wait_for(
                    self.llm.chat.completions.create(
                        model="gpt-4o",
                        messages=[{"role": "system", "content": recommendation_prompt}],
                        response_format={"type": "json_schema", "json_schema": schema}
                    ),
                    timeout=self.timeout
                )

                await self._update_status("Processing LLM response...", 0.8)

                # Parse response using Pydantic
                recommendations_response = RecommendationsResponse.parse_raw(response.choices[0].message.content)

                await self._update_status("Finalizing recommendations...", 0.9)

                return {
                    "status": "success",
                    "timestamp": datetime.utcnow().isoformat(),
                    "student_summary": student_summary,
                    "recommendations": recommendations_response.recommendations,
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
