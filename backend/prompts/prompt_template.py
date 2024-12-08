from llama_index.core.prompts.base import PromptTemplate

### Student Info Summary
student_info_summary_template = PromptTemplate("""
You are an AI academic advisor assistant tasked with analyzing student information to create an organized summary that will guide recommendation queries. 
Generate a structured summary using only the following sections, with no additional introduction or conclusion.
------------------------------------------------------------------------------------------------
Given student information:
{context}
------------------------------------------------------------------------------------------------
Format your response using exactly these headers:

1. CORE INTERESTS AND ABILITIES
- Connect and synthesize the stated academic interests, strengths, and demonstrated abilities
- Identify any clear themes or patterns that emerge from multiple data points
- Note any particularly strong alignments between interests and experiences

2. EXPERIENCE AND SKILLS CONTEXT
- Group related experiences and skills to show natural clusters
- Highlight any unique combinations of abilities or experiences
- Note the contexts where skills have been demonstrated

3. EXPRESSED VALUES AND PREFERENCES
- Synthesize stated preferences and decision-making factors
- Identify consistent themes in activities and choices
- Note any clear priorities that emerge from experiences

4. INFORMATION GAPS
- Note areas where additional information could expand search possibilities
- Identify any apparent disconnects that warrant broader exploration
- Flag aspects that could benefit from diverse perspectives

Begin directly with section 1 and end with section 4, without any additional text before or after.
""")

### Query Diversification
query_diversification_template = PromptTemplate("""
You are a query generation agent for an academic advising system. 
Your task is to generate diverse search queries for finding relevant alumni profiles using semantic similarity and keyword matching. 
The alumni profiles contain information like major, degree, job title, industry, and possibly some extra notes or comments.

------------------------------------------------------------------------------------------------
Student Profile Summary:
{summary}                                
------------------------------------------------------------------------------------------------

Generate 4 different types of search queries, with ONE query per type. Make each query a natural text phrase that captures the search intent:

1. DIRECT MATCH
Generate a focused query combining the student's primary field and role interests.

2. BROAD MATCH
Generate a query for related fields aligning with the student's skills.

3. CONTEXTUAL MATCH
Generate a query based on work style and impact preferences.

4. EXPLORATORY MATCH
Generate an unconventional query combining the student's skills with alternative applications.

Important:
- Create natural language phrases suitable for semantic search
- Avoid special syntax or operators
- Focus on concepts likely to appear in alumni profiles
- Ensure each query type offers a distinct search perspective
- Base queries strictly on the student's profile summary

Return just the four queries without numbering or categorization.
""")

### Internet Search
internet_search_template = PromptTemplate("""
You are a search query generation agent for an academic advising system. Your task is to generate two comprehensive search queries for finding enriching external information that complements alumni recommendations.

------------------------------------------------------------------------------------------------
Student Profile Summary:
{context}                                
------------------------------------------------------------------------------------------------

Generate 2 different types of search queries. Each query should be a detailed natural language phrase that integrates multiple aspects of the student's profile:

1. INDUSTRY TRENDS AND OPPORTUNITIES
Generate a comprehensive search query that combines:
- The student's primary field and interests
- Related or broader career paths
- Current industry developments
- Emerging opportunities and requirements
Format: Create a natural language search phrase that would surface articles, reports, and analyses about career trends and opportunities.

2. INSPIRATIONAL CAREER PATHS
Generate a search query focused on finding:
- Notable professionals in the student's field of interest
- Leaders who combined similar skills in innovative ways
- Success stories from related or adjacent fields
- Career progression examples that match student's values
Format: Create a natural language search phrase that would surface profiles, interviews, and career journey stories with actual names and details.

Important:
- Make queries detailed enough to find specific, relevant content
- Include key aspects from the student profile
- Focus on current and forward-looking information
- Ensure queries capture both traditional and innovative career perspectives
- Maintain natural language suitable for internet search engines

Return just the two queries without numbering or additional text.
""")

### Recommendation
recommendation_template = PromptTemplate("""
You are an AI academic advisor assistant tasked with providing academic pathway recommendations for advisors to use in student consultations. Generate recommendations in a specific JSON format that is analytical, evidence-based, and structured for advisor use.

------------------------------------------------------------------------------------------------
Student Profile Summary:
{context}                                
------------------------------------------------------------------------------------------------

Available Data for Recommendations:

ALUMNI PROFILES AND CAREER PATHS:
{alumni_profiles}

INDUSTRY INSIGHTS AND NOTABLE FIGURES:
{internet_insights}

------------------------------------------------------------------------------------------------

Generate a JSON response with 5 academic pathway recommendations (3 based on alumni pathways, 1 on emerging trends, 1 inspired by a notable figure).

Required JSON structure:
{{
  "recommendations": [
    {{
      "id": 1,
      "type": "alumni",  // Use "alumni", "trend", or "figure"
      "quickView": {{
        "title": "string", // Clear pathway name
        "summary": "string", // 2-3 sentences analyzing student fit
        "keyPoints": [  // Array of 3 key considerations
          "string",
          "string",
          "string"
        ],
        "nextStep": "string" // One concrete next discussion point
      }},
      "detailedView": {{
        "reasoning": "string", // Detailed analysis of fit and alignment
        "evidence": {{
          "alumniPatterns": "string", // Relevant alumni examples and patterns
          "industryContext": "string"  // Industry trends and developments
        }},
        "discussionPoints": [  // Array of specific points for advisor-student discussion
          "string",
          "string",
          "string"
        ]
      }}
    }}
  ]
}}

Requirements for content:
1. QuickView section:
   - Title: Clear and specific academic pathway name
   - Summary: Concise analysis of student fit using advisor-facing tone
   - KeyPoints: Three most important factors for consideration
   - NextStep: Specific discussion point or action for advisor

2. DetailedView section:
   - Reasoning: In-depth analysis without repeating quick view information
   - Evidence: Specific examples and data from alumni and industry sources
   - DiscussionPoints: Concrete topics for advisor-student conversations

Remember:
- Write for advisors as the primary audience ("the student" not "you/your")
- Focus on academic pathways that lead to career outcomes
- Keep suggestions broad enough for different universities
- Provide evidence-based recommendations
- Include specific discussion points for advisors
- Ensure JSON structure is valid with proper escaping of quotes

Follow these type distributions:
- Recommendations 1-3: type "alumni"
- Recommendation 4: type "trend"
- Recommendation 5: type "figure"

""")