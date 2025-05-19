import cohere
from typing import Dict, List, Optional
from program_model import ProgramModel

class AcademicDecisionModel:
    def __init__(self):
        self.program_model = ProgramModel()
        self.categories = [
            "program_info", "program_search", "eligibility", "duration", 
            "fees", "admission_process", "syllabus", "faculty", "exit"
        ]

    def classify_query(self, query: str) -> str:
        """Classify academic program-related queries into categories.

Preamble:
This classifier handles academic program queries with the following categories:
1. program_info: Requests for general program details
2. program_search: Queries about finding programs
3. eligibility: Questions about admission requirements
4. duration: Inquiries about program length
5. fees: Questions about program costs
6. admission_process: Application procedure queries
7. syllabus: Curriculum-related questions
8. faculty: Faculty/staff inquiries
9. exit: Exit/quit commands

Each category has specific keywords that trigger classification.
"""
        query = query.lower()
        
        # Check for exit commands
        if any(exit_word in query for exit_word in ["exit", "quit", "stop", "close"]):
            return "exit"
            
        # Check for program information requests
        if any(keyword in query for keyword in ["information about", "details of", "tell me about"]):
            return "program_info"
            
        # Check for program search
        if any(keyword in query for keyword in ["find", "search", "look for", "which programs"]):
            return "program_search"
            
        # Check for eligibility criteria
        if any(keyword in query for keyword in ["eligibility", "qualification", "requirements", "criteria"]):
            return "eligibility"
            
        # Check for duration queries
        if any(keyword in query for keyword in ["duration", "length", "how long", "years", "semesters"]):
            return "duration"
            
        # Check for fee-related queries
        if any(keyword in query for keyword in ["fee", "cost", "price", "tuition", "payment"]):
            return "fees"
            
        # Check for admission process
        if any(keyword in query for keyword in ["admission", "apply", "application", "process", "procedure"]):
            return "admission_process"
            
        # Check for syllabus queries
        if any(keyword in query for keyword in ["syllabus", "curriculum", "subjects", "courses", "topics"]):
            return "syllabus"
            
        # Check for faculty queries
        if any(keyword in query for keyword in ["faculty", "professor", "teacher", "instructor", "staff"]):
            return "faculty"
            
        # Default to program search if no specific category matched
        return "program_search"

    def process_query(self, query: str) -> Optional[Dict]:
        """Process the query based on its classification.

Preamble:
This processor takes classified queries and returns structured responses:
- For 'exit': Returns goodbye message
- For other categories: Returns action type and program details
- For ambiguous queries: Requests clarification about program name

Response format:
{
  "action": "category_name",
  "program": program_details,
  "query": original_query
}
"""
        category = self.classify_query(query)
        
        if category == "exit":
            return {"action": "exit", "message": "Goodbye!"}
            
        # Extract program name from query
        program_name = self._extract_program_name(query)
        
        if not program_name and category != "program_search":
            return {"action": "clarify", "message": "Which program are you asking about?"}
            
        program = None
        if program_name:
            program = self.program_model.get_program_by_name(program_name)
            
        # Handle duration queries specifically
        if category == "duration" and program:
            return {
                "action": "duration",
                "message": f"The duration of {program.name} is {program.duration} months.",
                "program": program,
                "query": query
            }
            
        # Handle fee queries specifically
        if category == "fees" and program:
            return {
                "action": "fees",
                "message": f"The fees for {program.name} are: {program.fee_structure}",
                "program": program,
                "query": query
            }
            
        # Handle general program info
        if program:
            return {
                "action": category,
                "message": f"Here's the information about {program.name}: {program.description}",
                "program": program,
                "query": query
            }
            
        return {
            "action": category,
            "program": program,
            "query": query
        }
        
    def _extract_program_name(self, query: str) -> Optional[str]:
        """Extract program name from query."""
        # This is a simple implementation - can be enhanced with NLP
        query = query.lower()
        
        # Look for patterns like "information about MBA" or "details of BCA program"
        for prefix in ["information about", "details of", "tell me about", "what is"]:
            if prefix in query:
                return query.split(prefix)[1].strip()
                
        return None