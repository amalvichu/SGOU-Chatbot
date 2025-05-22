from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import requests
from django.views.decorators.http import require_POST
from .llm_wrapper import query_local_llm


# Constants
UNIVERSITY_API_URL = "http://192.168.20.10:8000/api/programmes"
UNIVERSITY_API_KEY = "$2y$10$M0JLrgVmX2AUUqMZkrqaKOrgaMMaVFusOVjiXkVjc1YLyqcYFY9Bi"
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_API_KEY = "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"

def index(request):
    return render(request, 'index.html')


@csrf_exempt
@require_POST
def process_query(request):
    try:
        print(">>> Received a request")
        data = json.loads(request.body)
        user_query = data.get("query", "").strip()
        print(f">>> User query: {user_query}")

        if not user_query:
            return JsonResponse({"message": "Please enter a query."})

        # Use X-API-KEY header as per your JS example
        university_headers = {
            "X-API-KEY": UNIVERSITY_API_KEY,
            "Accept": "application/json",
        }

        # Call the university API with correct header
        university_response = requests.get(
            UNIVERSITY_API_URL,
            headers=university_headers,
            timeout=10
        )

        print(f">>> University API status: {university_response.status_code}")
        print(f">>> University API response (preview): {university_response.text[:200]}")

        if university_response.status_code != 200:
            return JsonResponse({"message": "Sorry, unable to fetch university data now."})

        uni_data = university_response.json()
        programs = uni_data.get('programme', [])
        if not isinstance(programs, list):
            return JsonResponse({"message": "Invalid data format received from university API."})

        prompt = build_prompt(user_query, programs)
        answer = call_openrouter_api(prompt)

        return JsonResponse({"message": answer})

    except Exception as e:
        print(">>> ERROR in process_query:", e)
        return JsonResponse({"message": "There was an error processing your request."})


def build_prompt(user_query, programs):
    program_summaries = []
    for p in programs:
        name = p.get('pgm_name', 'Unknown Program')
        desc = p.get('pgm_desc', 'No description')
        duration = p.get('pgm_year', 'N/A')
        program_summaries.append(f"{name} (Duration: {duration} year(s)) - {desc}")

    program_text = "\n".join(program_summaries[:10])  # Limit to first 10

    prompt = (
        "You are an expert assistant for Sreenarayanaguru Open University. "
        "Use the following program data to answer user questions:\n\n"
        f"{program_text}\n\n"
        f"User question: {user_query}\n"
        "Answer briefly and clearly."
    )
    return prompt


def call_openrouter_api(prompt):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    body = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "You are a helpful university chatbot assistant."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,
        "max_tokens": 400,
    }

    try:
        response = requests.post(OPENROUTER_API_URL, headers=headers, json=body, timeout=20)
        if response.status_code == 200:
            data = response.json()
            return data.get('choices', [{}])[0].get('message', {}).get('content', 'Sorry, no answer found.')
        else:
            print("OpenRouter API error:", response.status_code, response.text)
            return "Sorry, I am having trouble accessing the knowledge base right now."
    except Exception as e:
        print("Error calling OpenRouter:", e)
        return "Sorry, I'm unable to generate a response right now."


def fetch_programs(request):
    # URL of the actual SGOU program API endpoint
    sgou_api_url = 'https://192.168.20.10/api/programs'  # replace with actual endpoint
    
    try:
        # Call the SGOU API
        response = requests.get(sgou_api_url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Assuming the data structure contains a list of programs
        # Adjust 'programs' key below according to actual API response structure
        programs_list = data.get('programs', data)  # fallback to data if no 'programs' key
        
        # Add numbering
        for idx, program in enumerate(programs_list, start=1):
            program['number'] = idx
        
        return JsonResponse({'programs': programs_list})
    
    except requests.RequestException as e:
        # Handle errors, e.g. API not reachable or timeout
        return JsonResponse({
            'error': 'Failed to fetch programs from SGOU API.',
            'details': str(e)
        }, status=500)


def chatbot_response(request):
    if request.method == 'POST':
        user_message = json.loads(request.body).get('message', '')

        # Call local LLM
        llm_reply = query_local_llm(user_message)

        if llm_reply:
            return JsonResponse({'reply': llm_reply})
        else:
            return JsonResponse({'reply': 'Sorry, I couldn\'t process your request right now.'})
