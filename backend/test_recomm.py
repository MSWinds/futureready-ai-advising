# test_recommendation.py
import asyncio
import os
from dotenv import load_dotenv
from llama_index.llms.openai import OpenAI
from agents.recommendation_agent import RecommendationAgent
from datetime import datetime
from prompts.prompt_template import recommendation_template

# Load environment variables
load_dotenv()

# Mock search results that would come from search_agent
mock_search_results = {
    "queries": {
        "database_queries": [
            "Alumni who have worked as AI researchers or robotics engineers in tech companies",
            "Alumni with experience in mathematical modeling and programming",
            "Alumni who have mentored in programming or robotics",
            "Alumni who have worked on autonomous vehicles"
        ],
        "internet_queries": [
            "Latest trends in AI research and robotics engineering",
            "Notable careers in AI and autonomous vehicles"
        ]
    },
    "results": {
        "alumni_profiles": {
            "Alumni who have worked as AI researchers or robotics engineers in tech companies": [
                "Major: Computer Science; Degree: Ph.D; Job Title: Senior AI Researcher; Industry: Technology; Notes: Led autonomous systems team at major tech company",
                "Major: Robotics Engineering; Degree: M.S; Job Title: Robotics Engineer; Industry: Automation; Notes: Specializes in computer vision systems"
            ],
            "Alumni with experience in mathematical modeling and programming": [
                "Major: Applied Mathematics; Degree: M.S; Job Title: Machine Learning Engineer; Industry: Technology; Notes: Developed optimization algorithms for robotics applications",
                "Major: Mathematics; Degree: Ph.D; Job Title: Research Scientist; Industry: Technology; Notes: Focus on mathematical modeling for autonomous systems"
            ]
        },
        "internet_insights": {
            "Latest trends in AI research and robotics engineering": "The field of AI and robotics is rapidly evolving with increased focus on autonomous systems. Key trends include: 1) Integration of deep learning in robotics control systems, 2) Advanced computer vision applications, 3) Collaborative robots in manufacturing, 4) AI-powered decision making for autonomous vehicles.",
            "Notable careers in AI and autonomous vehicles": "Leading professionals in the field often combine strong technical skills with innovative problem-solving. Career paths include: Research Scientists at major tech companies, Robotics Engineers in manufacturing, AI Specialists in autonomous vehicle companies, and Technical Leaders in robotics startups."
        }
    }
}

# Mock student profile summary
mock_student_summary = """
Strong interest in AI and robotics, particularly excels at mathematical modeling and programming. 
Shows natural aptitude for problem-solving and algorithm development. Interested in working as 
an AI researcher or robotics engineer in tech companies. Also curious about autonomous vehicle 
development. Completed a summer internship at a local tech startup working on computer vision 
algorithms. Active member of robotics club, mentors high school students in programming, 
builds custom drones as a hobby.
"""

async def status_callback(message: str, progress: float):
    """Mock status callback to simulate frontend updates"""
    print(f"Status Update - Progress: {progress*100}% | Message: {message}")

class MockRecommendationAgent(RecommendationAgent):
    def __init__(self, llm):
        super().__init__(llm)
        self.timeout = 180  # Increase to 3 minutes for testing

    async def generate_recommendations(self, search_results: dict, student_summary: str) -> dict:
        try:
            # Print formatted inputs for debugging
            print("\nFormatted Alumni Results:")
            formatted_alumni = self._format_alumni_results(search_results["results"]["alumni_profiles"])
            print(formatted_alumni)

            print("\nFormatted Internet Results:")
            formatted_internet = self._format_internet_results(search_results["results"]["internet_insights"])
            print(formatted_internet)

            print("\nPrompt Template:")
            recommendation_prompt = recommendation_template.format(
                context=student_summary,
                alumni_profiles=formatted_alumni,
                internet_insights=formatted_internet
            )
            print(recommendation_prompt)

            # Debugging LLM call
            print("\nCalling LLM...")
            start_time = datetime.now()
            try:
                response = await asyncio.wait_for(
                    self.llm.acomplete(recommendation_prompt),
                    timeout=self.timeout
                )
                print(f"LLM response received after {(datetime.now() - start_time).total_seconds()} seconds")
                print("Raw LLM response:", response.text[:500] + "..." if len(response.text) > 500 else response.text)
            except asyncio.TimeoutError:
                print(f"LLM call timed out after {(datetime.now() - start_time).total_seconds()} seconds")
                raise

            return {"status": "success", "recommendations": response.text}
        except Exception as e:
            print(f"Error during recommendation generation: {str(e)}")
            return {"status": "error", "error": str(e)}

async def test_recommendation_agent():
    try:
        print("\nInitializing Recommendation Agent Test...")
        
        # Initialize OpenAI LLM
        llm = OpenAI(model="gpt-4", api_key=os.getenv("OPENAI_API_KEY"))
        
        # Use MockRecommendationAgent
        recommendation_agent = MockRecommendationAgent(llm=llm)
        recommendation_agent.set_status_callback(status_callback)
        
        print("\nGenerating Recommendations...")
        recommendations = await recommendation_agent.generate_recommendations(
            search_results=mock_search_results,
            student_summary=mock_student_summary
        )
        
        print("\nRecommendation Results:")
        print("\nStatus:", recommendations["status"])
        if recommendations["status"] == "success":
            print("\nGenerated Recommendations:", recommendations["recommendations"])
        else:
            print("\nError:", recommendations.get("error", "Unknown error occurred"))
        
    except Exception as e:
        print(f"Error during testing: {str(e)}")

if __name__ == "__main__":
    # Run the test
    asyncio.run(test_recommendation_agent())
