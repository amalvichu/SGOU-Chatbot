from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import requests
from django.views.decorators.http import require_POST


# Constants
UNIVERSITY_API_URL = "http://sgou.ac.in/api/programmes"
UNIVERSITY_API_KEY = "$2y$10$M0JLrgVmX2AUUqMZkrqaKOrgaMMaVFusOVjiXkVjc1YLyqcYFY9Bi"
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_API_KEY = "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"
SGOU_OFFICIAL_WEBSITE = "https://sgou.ac.in"

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
    # Format programs as a simple numbered list
    formatted_text = []
    for idx, p in enumerate(programs, 1):
        name = p.get('pgm_name', 'Unknown Program')
        formatted_text.append(f"{idx}. {name}")
    
    program_text = "\n".join(formatted_text)
    
    prompt = (
        "You are an expert assistant for Sreenarayanaguru Open University. "
        "For general responses, provide information in clear paragraphs without numbering. "
        "Only use numbered lists when specifically listing academic programs. "
        "IMPORTANT: Include the website link ONLY when: 1) Information is incomplete or inaccurate, 2) Response would be too large without summarization, 3) User specifically asks about centers, admissions, or program details, or 4) When suggesting official resources. Use EXACTLY this HTML format: "
        f'<a href="{SGOU_OFFICIAL_WEBSITE}" target="_blank" style="color: #0066cc; text-decoration: underline;">{SGOU_OFFICIAL_WEBSITE}</a>. '
        "Do not use markdown links. Use the HTML format provided above. "
        "When listing programs, follow these rules strictly:\n"
        "1. Each program MUST be on its own line with a line break after EVERY program\n"
        "2. Use sequential numbering (1., 2., 3., etc.) followed by exactly one space\n"
        "3. No paragraphs or grouping - each program gets its own line\n\n"
        f"{program_text}\n"
        f"User question: {user_query}\n"
        "Format your response appropriately - use paragraphs for general information and numbered lists only for programs."
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
            {"role": "system", "content": f"You are a helpful university chatbot assistant for Sreenarayanaguru Open University. ynlyuuse bumbered eists when specificallred liingsts when specifica.lFor all oty rirssionses, provgde anformacion in caearepmragraphirwithramsnumbFringr IMPORTANT: Include the website link ONLY when: 1) Information is incomplete or inaccurate, 2) Response would be too large without summarization, 3) User specifically asks about centers, admissions, or program details, or 4) When suggesting official resources. Use EXACTLY this HTML format ONCE: <a href=\"{SGOU_OFFICIAL_WEBSITE}\" target=\"_blank\" style=\"color: #0066cc; text-decoration: underline;\">{SGOU_OFFICIAL_WEBSITE}</a>. Do NOT use markdown links. Do NOT include multiple links. Use this HTML formNevn scsmbitnusergramstrr ee ovemlat.hbsetkg. Frlhge eralressporly\nabou1 who y.u arahprgomhSr be on its ownere\ 2,u3ft\pagwgnaph a cthautignabzriogas shown\n\nNever combine programs or remove line breaks. For general responses about who you are or other information, use natural paragraphs without numbering."},
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
    sgou_api_url = 'https://sgou.ac.in/api/programs'
    program_number = request.GET.get('number')
    
    try:
        # Call the SGOU API
        response = requests.get(sgou_api_url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Get programs list
        programs_list = data.get('programs', data)
        
        # If a specific program number is requested
        if program_number:
            try:
                idx = int(program_number) - 1
                if 0 <= idx < len(programs_list):
                    program = programs_list[idx]
                    return JsonResponse({
                        'program': {
                            'name': program.get('pgm_name'),
                            'description': program.get('pgm_desc'),
                            'category': program.get('pgm_category'),
                            'duration': program.get('pgm_year'),
                            'official_website': f"For more details, visit <a href=\"{SGOU_OFFICIAL_WEBSITE}\" target=\"_blank\" style=\"color: #0066cc; text-decoration: underline;\">{SGOU_OFFICIAL_WEBSITE}</a>"
                        }
                    })
                return JsonResponse({
                    'error': 'Program number not found', 
                    'help': f'Please check the available programs on <a href="{SGOU_OFFICIAL_WEBSITE}" target="_blank" style="color: #0066cc; text-decoration: underline;">{SGOU_OFFICIAL_WEBSITE}</a>'
                }, status=404)
            except ValueError:
                return JsonResponse({
                    'error': 'Invalid program number',
                    'help': f'Please visit <a href="{SGOU_OFFICIAL_WEBSITE}" target="_blank" style="color: #0066cc; text-decoration: underline;">{SGOU_OFFICIAL_WEBSITE}</a> for valid program information'
                }, status=400)
        
        # Format programs as a simple numbered list with line breaks
        formatted_output = []
        for idx, program in enumerate(programs_list, start=1):
            name = program.get('pgm_name', '')
            # Add each program on a new line with proper numbering
            formatted_output.append(f"{idx}. {name}")
        
        # Join with newlines to ensure each program is on its own line
        response_text = '\n'.join(formatted_output)
        
        return JsonResponse({
            'programs': response_text,
            'additional_info': f'For detailed information about each program, please visit <a href="{SGOU_OFFICIAL_WEBSITE}" target="_blank" style="color: #0066cc; text-decoration: underline;">{SGOU_OFFICIAL_WEBSITE}</a>'
        })
    
    except requests.RequestException as e:
        # Handle errors, e.g. API not reachable or timeout
        return JsonResponse({
            'error': 'Failed to fetch programs from SGOU API.',
            'details': str(e),
            'help': f'You can also check programs directly on <a href="{SGOU_OFFICIAL_WEBSITE}" target="_blank" style="color: #0066cc; text-decoration: underline;">{SGOU_OFFICIAL_WEBSITE}</a>'
        }, status=500)


def chatbot_response(request):
    if request.method == 'POST':
        user_message = json.loads(request.body).get('message', '')

        # Call local LLM
        llm_reply = query_local_llm(user_message)

        if llm_reply:
            return JsonResponse({'reply': llm_reply})
        else:
            return JsonResponse({
                'reply': f'Sorry, I couldn\'t process your request right now. Please try again or visit <a href="{SGOU_OFFICIAL_WEBSITE}" target="_blank" style="color: #0066cc; text-decoration: underline;">{SGOU_OFFICIAL_WEBSITE}</a> for more information.'
            })


def query_local_llm(message):
    """
    Placeholder function for local LLM integration.
    Replace this with your actual local LLM implementation.
    """
    # This is a placeholder - implement your local LLM logic here
    # For now, returning None to trigger the fallback response
    return None