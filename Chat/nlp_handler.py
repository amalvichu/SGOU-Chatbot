# Chat/nlp_handler.py

import re

def extract_keywords(query):
    # Naive extraction (can be replaced with a real NLP parser)
    query = query.lower()
    keywords = {}
    
    if "program" in query or "course" in query:
        keywords['type'] = 'program'
    elif "certification" in query:
        keywords['type'] = 'certification'
    elif "assignment" in query:
        keywords['type'] = 'assignment'
    elif "center" in query:
        keywords['type'] = 'center'
    elif "learning" in query or "material" in query:
        keywords['type'] = 'learning'
    
    # Extract possible program names
    program_match = re.search(r"(ba|ma|bsc|msc|bcom|mcom)", query)
    if program_match:
        keywords['program'] = program_match.group(1).upper()
    
    return keywords
