from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import requests
import os
from django.views.decorators.http import require_POST
from dotenv import load_dotenv

load_dotenv()

# Load environment variables
UNIVERSITY_API_URL = os.getenv("UNIVERSITY_API_URL")
UNIVERSITY_API_KEY = os.getenv("UNIVERSITY_API_KEY")
CENTERS_API_URL = os.getenv("CENTERS_API_URL")
GROQ_API_URL = os.getenv("GROQ_API_URL")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

SGOU_OFFICIAL_WEBSITE = "https://sgou.ac.in"

def index(request):
    return render(request, "index.html")

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
        centers = []
        programs = []

        if any(keyword in user_query.lower() for keyword in ["center", "centre", "regional center", "study center"]):
            print(">>> Center query detected, fetching centers...")
            centers_response = fetch_centers(request)
            print(f">>> Centers response status: {centers_response.status_code}")
            
            if centers_response.status_code == 200:
                centers_data = json.loads(centers_response.content)
                print(f">>> Centers response data: {centers_data}")
                centers = centers_data.get("centers", [])
                print(f">>> Extracted centers: {centers}")
                
                # For center queries, return the formatted centers directly
                if centers:
                    centers_html = "<ol>" + "".join([f"<li>{center}</li>" for center in centers]) + "</ol>"
                    return JsonResponse({"message": centers_html})
                else:
                    return JsonResponse({"message": "No centers found."})
            else:
                print(f">>> Centers fetch failed: {centers_response.content}")
                return centers_response # Return error response from fetch_centers
        else:
            university_response = requests.get(
                UNIVERSITY_API_URL, headers=university_headers, timeout=10
            )

            print(f">>> University API status: {university_response.status_code}")
            print(
                f">>> University API response (preview): {university_response.text[:200]}")

            if university_response.status_code != 200:
                return JsonResponse(
                    {"message": "Sorry, unable to fetch university data now."}
                )

            uni_data = university_response.json()
            programs = uni_data.get("programme", [])
            if not isinstance(programs, list):
                return JsonResponse(
                    {"message": "Invalid data format received from university API."}
                )

        prompt = build_prompt(user_query, programs, centers)
        answer = call_groq_api(prompt, programs, centers)

        return JsonResponse({"message": answer})

    except Exception as e:
        print(">>> ERROR in process_query:", e)
        return JsonResponse({"message": "There was an error processing your request."})

def build_prompt(user_query, programs, centers=None):
    # Only include program list if user explicitly asks about programs
    program_text = ""
    if any(keyword in user_query.lower() for keyword in ["program", "course", "study", "list programs", "show programs"]):
        # Format programs as HTML ordered list
        program_html_items = []
        for program in programs:
            program_name = program.get('pgm_name', 'Unknown')
            program_html_items.append(f"<li>{program_name}</li>")
        
        program_text = f"Available Programs (format as HTML ordered list):\n<ol>{''.join(program_html_items)}</ol>\n\n"

    centers_text = ""
    if centers:
        # Format centers as HTML ordered list
        centers_html_items = []
        for center in centers:
            centers_html_items.append(f"<li>{center}</li>")
        
        centers_text = f"Available Centers (format as HTML ordered list):\n<ol>{''.join(centers_html_items)}</ol>\n\n"

    prompt = (
        "You are an expert assistant for Sreenarayanaguru Open University. "
        "For general responses, provide information in clear paragraphs without numbering. "
        "Do NOT offer or list academic programs unless the user explicitly asks for them. "
        "Only use numbered lists when specifically listing academic programs. "
        "IMPORTANT: When providing center details, format them as an HTML ordered list using <ol> and <li> tags. "
        "Each center should be in its own <li> tag with all information (name, address, headname, headnumber, headmail) properly formatted with line breaks using <br> tags. It must display all the name of the center"
        "Include the website link ONLY when: 1) Information is genuinely incomplete or inaccurate, 2) Response would be too large without summarization, 3) User specifically asks about centers, admissions, or program details, or 4) When suggesting official resources. Use EXACTLY this HTML format: "
        f'<a href="{SGOU_OFFICIAL_WEBSITE}" target="_blank" style="color: #0066cc; text-decoration: underline;">{SGOU_OFFICIAL_WEBSITE}</a>. '
        "Do not use markdown links. Use the HTML format provided above. "
        "When listing programs, follow these rules strictly:\n"
        "1. Format as HTML ordered list using <ol> and <li> tags\n"
        "2. Each program must be in its own <li> tag\n"
        "3. Include only the program name within each <li> tag\n"
        "4. Do not add any additional text or formatting within program names\n"
        "DO NOT add any introductory sentences or paragraphs before the ordered list of programs. Start directly with the HTML <ol> tag.\n\n"
        "When listing centers, follow these rules strictly:\n"
        "1. Format as HTML ordered list using <ol> and <li> tags\n"
        "2. Each center must be in its own <li> tag\n"
        "3. Include all center information with proper HTML formatting\n"
        "4. Use <br> tags for line breaks within each center's information\n"
        "DO NOT add any introductory sentences or paragraphs before the ordered list of centers. Start directly with the HTML <ol> tag.\n\n"
        f"{program_text}"
        f"{centers_text}"
        f"User question: {user_query}\n"
        "Format your response appropriately - use paragraphs for general information and HTML ordered lists for both programs and centers. "
        "Avoid asking follow-up questions that require a 'yes' or 'no' response. Provide direct and complete answers to user queries."
        "Do not include phrases like 'We offer a wide range of academic programs. If you would like to know more about our programs, here is a list of our programs:' unless the user explicitly asks for programs."
    )
    return prompt

def call_groq_api(prompt, programs_data, centers_data=None):
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    messages = [
        {
            "role": "system",
            "content": "You are an official representative of Sreenarayanaguru Open University. Use 'we' instead of repeatedly saying the university name. Be direct, concise, and avoid conversational filler. Provide complete answers without asking follow-up questions that require 'yes' or 'no' responses. If a university website is mentioned, ensure it is provided as a clickable link. When asked about program duration, respond only with 'The duration is X years.' where X is the number. When listing centers, format them as an HTML ordered list using <ol> and <li> tags with proper formatting including <br> tags for line breaks within each center's information. When listing programs, format them as an HTML ordered list using <ol> and <li> tags with each program name in its own <li> tag. Only display program details when explicitly asked for a list, and then present them in HTML ordered list format.",
        },
        {"role": "user", "content": prompt},
    ]

    if centers_data:
        messages.append({"role": "system", "content": f"Here is the list of centers to format as HTML ordered list: {centers_data}"})

    # INCREASED max_tokens for better center display
    body = {
        "model": "llama3-70b-8192",
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 1500,  # Increased from 500 to 1500
    }

    try:
        response = requests.post(GROQ_API_URL, headers=headers, json=body, timeout=30)  # Increased timeout
        if response.status_code == 200:
            data = response.json()
            return (
                data.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "Sorry, no answer found.")
            )
        else:
            print("Groq API error:", response.status_code, response.text)
            return "Sorry, I am having trouble accessing the knowledge base right now."
    except Exception as e:
        print("Error calling Groq API:", e)
        return "Sorry, I'm unable to generate a response right now."

def fetch_centers(request):
    try:
        headers = {
            "X-API-KEY": UNIVERSITY_API_KEY,
            "Accept": "application/json",
        }
        
        response = requests.get(CENTERS_API_URL, headers=headers, timeout=10)
        
        response.raise_for_status()
        centers_data = response.json()
        
        # Debug: Print the raw API response
        print(f">>> Raw centers API response: {centers_data}")
        
        # Try different possible keys for centers data
        centers_list = centers_data.get("rc", [])
        if not centers_list:
            centers_list = centers_data.get("centers", [])
        if not centers_list:
            centers_list = centers_data.get("data", [])
        if not centers_list and isinstance(centers_data, list):
            centers_list = centers_data
            
        print(f">>> Found {len(centers_list)} centers in API response")
            
        if not centers_list:
            return JsonResponse({"message": "No centers found in API response."})

        formatted_centers = []
        for idx, center in enumerate(centers_list):
            print(f">>> Processing center {idx + 1}: {center}")
            
            # Try different possible field names
            name = (center.get('rcname') or 
                   center.get('name') or
                   center.get('center_name') or
                   'Unknown Center')
            
            address = (center.get('rcaddress') or 
                      center.get('address') or
                      center.get('center_address') or
                      'N/A')

            headname = (center.get('headname') or 
                       center.get('director_name') or
                       center.get('head_name') or
                       'N/A')
            
            headnumber = (center.get('headnumber') or
                         center.get('director_phone') or
                         center.get('phone') or
                         center.get('contact_number') or
                         'N/A')

            headmail = (center.get('headmail') or 
                       center.get('director_email') or
                       center.get('email') or
                       center.get('contact_email') or
                       'N/A')

            # Only include centers with a known name
            if name != 'Unknown Center' and name != 'N/A':
                # Format each center with HTML formatting for better display
                center_html = f"<strong>{name}</strong><br>Address: {address}<br>RC Director: {headname}<br>Number: {headnumber}<br>Email: <a href='mailto:{headmail}' style='color: #0066cc;'>{headmail}</a>"
                formatted_centers.append(center_html)
                print(f">>> Formatted center {idx + 1}: {center_html[:100]}...")
        
        print(f">>> Total formatted centers: {len(formatted_centers)}")
        return JsonResponse({"centers": formatted_centers})

    except requests.exceptions.RequestException as e:
        print(f">>> Error fetching centers: {e}")
        return JsonResponse({"message": "Sorry, unable to fetch center data now."}, status=500)
    except ValueError as e:
        print(f">>> Error parsing centers JSON: {e}")
        return JsonResponse({"message": "Sorry, invalid center data received."}, status=500)
    except Exception as e:
        print(f">>> An unexpected error occurred: {e}")
        return JsonResponse({"message": "An unexpected error occurred while fetching centers."}, status=500)

def fetch_programs(request):
    # URL of the actual SGOU program API endpoint
    sgou_api_url = "https://sgou.ac.in/api/programs"
    program_number = request.GET.get("number")

    try:
        # Call the SGOU API
        response = requests.get(sgou_api_url, timeout=10)
        response.raise_for_status()
        data = response.json()

        # Get programs list
        programs_list = data.get("programs", data)

        # If a specific program number is requested
        if program_number:
            try:
                idx = int(program_number) - 1
                if 0 <= idx < len(programs_list):
                    program = programs_list[idx]
                    return JsonResponse(
                        {
                            "program": {
                                "name": program.get("pgm_name"),
                                "description": program.get("pgm_desc"),
                                "category": program.get("pgm_category"),
                                "duration": program.get("pgm_year"),
                                "official_website": f'For more details, visit <a href="{SGOU_OFFICIAL_WEBSITE}" target="_blank" style="color: #0066cc; text-decoration: underline;">{SGOU_OFFICIAL_WEBSITE}</a>',
                            }
                        }
                    )
                return JsonResponse(
                    {
                        "error": "Program number not found",
                        "help": f'Please check the available programs on <a href="{SGOU_OFFICIAL_WEBSITE}" target="_blank" style="color: #0066cc; text-decoration: underline;">{SGOU_OFFICIAL_WEBSITE}</a>',
                    },
                    status=404,
                )
            except ValueError:
                return JsonResponse(
                    {
                        "error": "Invalid program number",
                        "help": f'Please visit <a href="{SGOU_OFFICIAL_WEBSITE}" target="_blank" style="color: #0066cc; text-decoration: underline;">{SGOU_OFFICIAL_WEBSITE}</a> for valid program information',
                    },
                    status=400,
                )

        # Format programs as HTML ordered list
        program_html_items = []
        for program in programs_list:
            name = program.get("pgm_name", "")
            if name:  # Only add if name exists
                program_html_items.append(f"<li>{name}</li>")

        # Create HTML ordered list
        response_html = f"<ol>{''.join(program_html_items)}</ol>"

        return JsonResponse(
            {
                "programs": response_html,
                "additional_info": f'For detailed information about each program, please visit <a href="{SGOU_OFFICIAL_WEBSITE}" target="_blank" style="color: #0066cc; text-decoration: underline;">{SGOU_OFFICIAL_WEBSITE}</a>',
            }
        )

    except requests.RequestException as e:
        # Handle errors, e.g. API not reachable or timeout
        return JsonResponse(
            {
                "error": "Failed to fetch programs from SGOU API.",
                "details": str(e),
                "help": f'You can also check programs directly on <a href="{SGOU_OFFICIAL_WEBSITE}" target="_blank" style="color: #0066cc; text-decoration: underline;">{SGOU_OFFICIAL_WEBSITE}</a>',
            },
            status=500,
        )

def chatbot_response(request):
    if request.method == "POST":
        user_message = json.loads(request.body).get("message", "")

        # Call local LLM
        llm_reply = query_local_llm(user_message)

        if llm_reply:
            return JsonResponse({"reply": llm_reply})
        else:
            return JsonResponse(
                {
                    "reply": f'Sorry, I couldn\'t process your request right now. Please try again or visit <a href="{SGOU_OFFICIAL_WEBSITE}" target="_blank" style="color: #0066cc; text-decoration: underline;">{SGOU_OFFICIAL_WEBSITE}</a> for more information.'
                }
            )

def query_local_llm(message):
    """
    Placeholder function for local LLM integration.
    Replace this with your actual local LLM implementation.
    """
    # This is a placeholder - implement your local LLM logic here
    # For now, returning None to trigger the fallback response
    return None