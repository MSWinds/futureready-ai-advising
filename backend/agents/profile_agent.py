from typing import List, Dict
from prompts.prompt_template import student_info_summary_template
from typing import Dict
from pydantic import BaseModel, Field
from llama_index.llms.openai import OpenAI

class StudentInfo(BaseModel):
    """Pydantic model for student information"""
    academic_interests: str = Field(..., description="Student's primary academic interests and strengths")
    career_paths: str = Field(..., description="Specific career paths or industries of interest")
    course_preferences: str = Field(..., description="Favorite and least favorite courses")
    experience: str = Field(..., description="Relevant experience")
    skills: str = Field(..., description="Unique skills or achievements")
    extracurriculars: str = Field(..., description="Key extracurricular activities or passion projects")
    decision_factors: str = Field(..., description="Important factors in academic/career decisions")
    advisor_notes: str = Field(..., description="Additional observations or context")

def format_context(student_info: Dict[str, str]) -> str:
    """Format student info into context string for the template"""
    context_parts = []
    for field, value in student_info.items():
        if value and value.strip():
            readable_field = field.replace('_', ' ').title()
            context_parts.append(f"{readable_field}:\n{value}\n")
    return "\n".join(context_parts)

# Profile Agent
class ProfileAgent:
    def __init__(self, llm):
        """Initialize the profile agent with the LLM instance"""
        self.llm = llm

    async def generate_profile_summary(self, student_info: StudentInfo) -> str:
        """
        Generate a summary of the student profile
        
        Args:
            student_info: StudentInfo object containing all student information
        
        Returns:
            str: Generated summary of the student profile
        """
        try:
            # Convert Pydantic model to dict and format context
            student_info_dict = student_info.dict()
            context = format_context(student_info_dict)

            # Generate summary using the provided LLM
            llm_response = self.llm.complete(
                student_info_summary_template.format(context=context)
            )

            return llm_response.text.strip()

        except Exception as e:
            raise RuntimeError(f"Error generating profile summary: {str(e)}")