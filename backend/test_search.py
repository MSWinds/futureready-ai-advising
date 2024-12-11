# test.py
import asyncio
import os
from dotenv import load_dotenv
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.vector_stores.postgres import PGVectorStore
from llama_index.core import VectorStoreIndex
from tavily import TavilyClient
from sqlalchemy.engine.url import make_url
from agents.search_agent import SearchAgent

# Load environment variables
load_dotenv()

async def init_components():
    # Initialize OpenAI
    llm = OpenAI(model="gpt-4", api_key=os.getenv("OPENAI_API_KEY"))
    
    # Database and vector store setup
    connection_string = os.getenv("DB_CONNECTION")
    url = make_url(connection_string)
    
    # Create embedding model
    embedding_model = OpenAIEmbedding(model="text-embedding-3-large")
    
    # Set up vector store
    vector_store = PGVectorStore.from_params(
        database='ai_advising_db',
        host=url.host,
        password=url.password,
        port=url.port,
        user=url.username,
        table_name="alumni_records",
        embed_dim=3072,
        hybrid_search=True,
        text_search_config="english",
    )
    
    # Create hybrid index
    hybrid_index = VectorStoreIndex.from_vector_store(
        vector_store=vector_store,
        embed_model=embedding_model
    )
    
    # Initialize Tavily client
    tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
    
    return llm, hybrid_index, tavily_client

async def test_search_agent():
    try:
        # Initialize components
        print("Initializing components...")
        llm, hybrid_index, tavily_client = await init_components()
        
        # Create search agent
        search_agent = SearchAgent(llm=llm, hybrid_index=hybrid_index, tavily_client=tavily_client)
        
        # Test profile summary
        test_summary = """
        1. CORE INTERESTS AND ABILITIES
        The student has a strong interest in AI and robotics, with a particular emphasis on mathematical modeling and programming. This interest is complemented by a natural aptitude for problem-solving and algorithm development, suggesting a strong alignment between their interests and abilities. The student's academic interests and strengths seem to be primarily focused on technical areas, with a clear theme of AI and robotics emerging from the data.

        2. EXPERIENCE AND SKILLS CONTEXT
        The student's skills in mathematical modeling and programming, combined with their problem-solving abilities, form a natural cluster that is highly relevant to their interest in AI and robotics. These skills have likely been demonstrated and honed through academic coursework and projects. The student's interest in autonomous vehicle development suggests a unique combination of abilities and experiences, potentially involving real-world applications of AI and robotics.

        3. EXPRESSED VALUES AND PREFERENCES
        The student has expressed a clear preference for working in tech companies as an AI researcher or robotics engineer. This suggests a value placed on technical roles and a desire to contribute to the field of AI and robotics. The student's curiosity about autonomous vehicle development also indicates an openness to exploring new applications of their skills and interests.

        4. INFORMATION GAPS
        While the student's technical interests and abilities are well-documented, there is less information about their experiences and interests outside of these areas. The advisor's note suggests that the student could benefit from more interdisciplinary exposure, indicating a potential gap in their experiences. Additionally, the student's hesitation to consider paths outside of pure technical roles suggests a potential disconnect that could be explored further. This could involve exploring the student's interests in areas such as business, policy, or design, which could complement their technical skills and open up new career paths.
        """
        
        print("\nExecuting combined search...")
        search_results = await search_agent.execute_combined_search(test_summary)
        
        # Print results
        print("\nSearch Results:")
        print("\nQueries Generated:")
        print("Database Queries:", search_results["queries"]["database_queries"])
        print("Internet Queries:", search_results["queries"]["internet_queries"])
        
        print("\nAlumni Profiles:")
        for query, results in search_results["results"]["alumni_profiles"].items():
            print(f"\nQuery: {query}")
            for i, result in enumerate(results, 1):
                print(f"Result {i}:", result)
        
        print("\nInternet Insights:")
        for question, answer in search_results["results"]["internet_insights"].items():
            print(f"\nQuestion: {question}")
            print(f"Answer: {answer}")
            
    except Exception as e:
        print(f"Error during testing: {str(e)}")

if __name__ == "__main__":
    # Run the test
    asyncio.run(test_search_agent())