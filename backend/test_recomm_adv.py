import asyncio
import os
from dotenv import load_dotenv
from datetime import datetime
from openai import AsyncOpenAI
from agents.recommendation_agent import RecommendationAgent
from prompts.prompt_template import recommendation_template

# Load environment variables
load_dotenv()

# Mock search results to simulate input
mock_search_results = {
    "queries": {
        "database_queries": [
            "Alumni who have worked in AI research",
            "Alumni with experience in robotics development"
        ],
        "internet_queries": [
            "Current trends in AI research",
            "Top careers in robotics engineering"
        ]
    },
    "results": {
        "alumni_profiles": {
            "Alumni who have worked in AI research": [
                "Name: John Doe; Degree: Ph.D.; Job Title: AI Researcher; Notes: Published work on neural networks.",
                "Name: Jane Smith; Degree: M.S.; Job Title: Data Scientist; Notes: Specializes in AI applications."
            ],
            "Alumni with experience in robotics development": [
                "Name: Emily Johnson; Degree: M.S.; Job Title: Robotics Engineer; Notes: Built autonomous systems.",
                "Name: Michael Brown; Degree: B.S.; Job Title: Mechanical Engineer; Notes: Robotics design expert."
            ]
        },
        "internet_insights": {
            "Current trends in AI research": "1. Use of LLMs in robotics. 2. Improvements in reinforcement learning.",
            "Top careers in robotics engineering": "Popular careers include AI Robotics Engineer, Control Systems Specialist."
        }
    }
}

# Mock student summary
mock_student_summary = """
Student Profile:
- Strong background in AI research and robotics.
- Interest in working with autonomous systems and machine learning.
- Experience includes university robotics club and internship in AI applications.
"""

# Mock status callback
async def status_callback(message: str, progress: float):
    """Mock status callback to display status updates."""
    print(f"STATUS [{progress*100:.0f}%]: {message}")

# Test function
async def test_recommendation_agent():
    try:
        print("\n--- INITIALIZING TEST ---")
        
        # Load OpenAI LLM (using gpt-4o for structured output)
        llm = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Initialize Recommendation Agent
        recommendation_agent = RecommendationAgent(llm=llm)
        recommendation_agent.set_status_callback(status_callback)
        
        print("\n--- GENERATING RECOMMENDATIONS ---")
        recommendations = await recommendation_agent.generate_recommendations(
            search_results=mock_search_results,
            student_summary=mock_student_summary
        )

        print("\n--- RECOMMENDATION OUTPUT ---")
        print("Status:", recommendations["status"])
        print("Timestamp:", recommendations["timestamp"])
        if recommendations["status"] == "success":
            print("\nRecommendations:")
            for i, rec in enumerate(recommendations["recommendations"], 1):
                print(f"\nRecommendation {i}:")
                print("Type:", rec.type)
                print("Title:", rec.quickView.title)
                print("Summary:", rec.quickView.summary)
                print("Key Points:", ", ".join(rec.quickView.keyPoints))
                print("Next Step:", rec.quickView.nextStep)
        else:
            print("Error:", recommendations["error"])

    except Exception as e:
        print(f"Test failed due to: {e}")

if __name__ == "__main__":
    asyncio.run(test_recommendation_agent())

