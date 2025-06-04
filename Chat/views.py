from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import requests
import os
import logging
from django.views.decorators.http import require_POST
from dotenv import load_dotenv
import re
from difflib import SequenceMatcher

load_dotenv()

# Load environment variables
UNIVERSITY_API_URL = os.getenv("UNIVERSITY_API_URL")
UNIVERSITY_API_KEY = os.getenv("UNIVERSITY_API_KEY")
CENTERS_API_URL = os.getenv("CENTERS_API_URL")
LSC_API_URL = os.getenv("LSC_API_URL")
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
        
        # First check questioners API
        try:
            api_url = "http://192.168.20.2:8000/api/questioners"
            response = requests.get(api_url)
            response.raise_for_status()
            questions_data = response.json()
            print(f"Debug: questions_data from API: {questions_data}")
            
            print(f"Checking API for matches to query: {user_query}")
            for item in questions_data.get('question', []):
                if "question" in item and "answer" in item:
                    print(f"Comparing with API question: {item['question']}")
                    
                    # Prioritize exact matches
                    if user_query.lower() == item["question"].lower():
                        print(f"Exact API match found for: {user_query}")
                        answer = item['answer']
                        print(f"API answer: {answer}")
                        return JsonResponse({"answer": answer}, status=200)
                    
                    # Similarity check with higher threshold for fee-related queries
                    similarity_threshold = 0.8 if 'fee' in user_query.lower() else 0.7
                    similarity = SequenceMatcher(None, user_query.lower(), item["question"].lower()).ratio()
                    print(f"Similarity score: {similarity:.2f}")
                    
                    if similarity > similarity_threshold:
                        print(f"Similar API match found (score: {similarity:.2f}): {item['question']}")
                        answer = item['answer']
                        print(f"API answer: {answer}")
                        return JsonResponse({"answer": answer}, status=200)
            
            print("No matching questions found in API")
        except Exception as e:
            print(f"Error checking questioners API: {e}")
            # Continue to normal processing if API check fails


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

        # Fetch all regional centers once
        rc_name_mapping = {}
        try:
            centers_response = fetch_centers(request)
            if centers_response.status_code == 200:
                centers_data = json.loads(centers_response.content)
                print(f"Debug: centers_data in process_query: {centers_data}")
                # The fetch_centers function now returns a JsonResponse with "formatted_centers" and "raw_centers" keys
                formatted_centers_list = centers_data.get("formatted_centers", [])
                raw_centers_list = centers_data.get("raw_centers", [])
                print(f"Debug: formatted_centers_list extracted in process_query: {formatted_centers_list}")
                print(f"Debug: raw_centers_list extracted in process_query: {raw_centers_list}")

                for center in raw_centers_list:
                    rc_id = center.get("id")
                    rc_name = (
                        center.get("rcname")
                        or center.get("name")
                        or center.get("center_name")
                    )
                    if rc_id and rc_name:
                        rc_name_mapping[rc_id] = rc_name
        except Exception as e:
            print(f"Error fetching regional centers for mapping: {e}")

        try:  # Added try block
            normalized_query = user_query.lower()
            center_keywords = [
                "center",
                "centre",
                "regional center",
                "study center",
                "cneters",
                "centres",
                "cenrets",
            ]
            program_keywords = [
                "program",
                "course",
                "study",
                "list programs",
                "show programs",
                "progams",
                "courses",
            ]
            lsc_keywords = [
                "lsc",
                "learning support center",
                "study center",
                "lscs",
                "learning support centers",
            ]
            regional_center_query_match = re.search(
                r"lsc(?:'s)? under regional center (\w+)", normalized_query
            )

            if regional_center_query_match:
                regional_center_name = regional_center_query_match.group(1)
                print(
                    f">>> LSC query for specific regional center detected: {regional_center_name}"
                )
                lsc_data = fetch_lsc_data(regional_center_name)
                if lsc_data:
                    lsc_list_html = f"Here are the LSCs under {regional_center_name} Regional Center:\n<ol>"
                    for lsc in lsc_data:
                        rc_id = lsc.get("lscrc")
                        if isinstance(rc_id, str) and rc_id.isdigit():
                            rc_id = int(rc_id)
                        elif not isinstance(rc_id, int):
                            rc_id = None  # Set to None if not a valid ID

                        # ✅ Use rc_name_mapping to get the rcname
                        rc_name = rc_name_mapping.get(rc_id, "N/A")

                        lsc_list_html += f"<li><strong>{lsc['lscname']}</strong><br>Address: {lsc['lscaddress']}<br>Contact: {lsc['lscnumber']}<br>Coordinator: {lsc['coordinatorname']}<br>Email: <a href='mailto:{lsc['coordinatormail']}' style='color: #0066cc;'>{lsc['coordinatormail']}</a><br>RC: {rc_id}<br>RC Name: {rc_name}</li>"
                    lsc_list_html += "</ol>"
                    return JsonResponse({"message": lsc_list_html})
                else:
                    return JsonResponse(
                        {"message": "Sorry, I couldn't fetch LSC data at the moment."}
                    )

            elif any(keyword in normalized_query for keyword in center_keywords):
                # If the query is about centers, display the formatted list
                if formatted_centers_list:
                    formatted_centers_html = "Here are the Regional Centers:\n<ol>"
                    for center_html in formatted_centers_list:
                        formatted_centers_html += f"<li>{center_html}</li>"
                    formatted_centers_html += "</ol>"
                    return JsonResponse({"message": formatted_centers_html})
                else:
                    return JsonResponse({"message": "Sorry, I couldn't fetch regional center data at the moment."})
            elif any(keyword in normalized_query for keyword in lsc_keywords):
                print(">>> General LSC query detected, fetching all LSCs...")
                lsc_data = fetch_lsc_data()
                if lsc_data:
                    all_lscs_html = "Here are the Learning Support Centers:\n<ol>"
                    for lsc in lsc_data:
                        rc_id = lsc.get("lscrc")
                        # Ensure rc_id is an integer for mapping lookup
                        if isinstance(rc_id, str) and rc_id.isdigit():
                            rc_id = int(rc_id)
                        elif not isinstance(rc_id, int):
                            rc_id = None  # Set to None if not a valid ID

                        rc_name = rc_name_mapping.get(rc_id, "N/A")  # Use the mapping
                        print(
                            f"DEBUG: LSC RC ID: {lsc.get('lscrc')}, Processed RC ID: {rc_id}, RC Name from mapping: {rc_name}"
                        )
                        all_lscs_html += f"<li><strong>{lsc['lscname']}</strong><br>Address: {lsc['lscaddress']}<br>Contact: {lsc['lscnumber']}<br>Coordinator: {lsc['coordinatorname']}<br>Email: <a href='mailto:{lsc['coordinatormail']}' style='color: #0066cc;'>{lsc['coordinatormail']}</a><br>RC: {rc_id}<br>RCNAME: {rc_name}</li>"
                    all_lscs_html += "</ol>"
                    return JsonResponse({"message": all_lscs_html})
                else:
                    return JsonResponse(
                        {"message": "Sorry, I couldn't fetch LSC data at the moment."}
                    )
        except Exception as e:  # Corrected indentation
            print(f"Error fetching regional centers for mapping: {e}")

        # Normalize user query for keyword detection to handle typos
        normalized_query = user_query.lower()

        # Check for clarification needed for Honours programs
        if request.session.get('clarification_needed'):
            print(f">>> Clarification needed for Honours program. User query: {user_query}")
            if normalized_query == 'yes':
                program = request.session.get('honours_program')
                del request.session['clarification_needed']
                del request.session['honours_program']
                del request.session['regular_program']
                if program:
                    program_details_html = f"<h3>{program.get('pgm_name', 'N/A')}</h3>"
                    program_details_html += f"<p><strong>Program Code:</strong> {program.get('pgm_code', 'N/A')}</p>"
                    program_details_html += f"<p><strong>Category:</strong> {program.get('pgm_category', 'N/A')}</p>"
                    program_details_html += f"<p><strong>Duration:</strong> {program.get('pgm_duration', 'N/A')}</p>"
                    program_details_html += f"<p><strong>Description:</strong> {program.get('pgm_desc', 'N/A')}</p>"
                    return JsonResponse({"message": program_details_html})
                else:
                    return JsonResponse({"message": "Sorry, I couldn't find the Honours program details."})
            elif normalized_query == 'no':
                program = request.session.get('regular_program')
                del request.session['clarification_needed']
                del request.session['honours_program']
                del request.session['regular_program']
                if program:
                    program_details_html = f"<h3>{program.get('pgm_name', 'N/A')}</h3>"
                    program_details_html += f"<p><strong>Program Code:</strong> {program.get('pgm_code', 'N/A')}</p>"
                    program_details_html += f"<p><strong>Category:</strong> {program.get('category', 'N/A')}</p>"
                    program_details_html += f"<p><strong>Duration:</strong> {program.get('duration', 'N/A')}</p>"
                    program_details_html += f"<p><strong>Eligibility:</strong> {program.get('eligibility', 'N/A')}</p>"
                    program_details_html += f"<p><strong>Description:</strong> {program.get('description', 'N/A')}</p>"
                    return JsonResponse({"response": program_details_html})
                else:
                    return JsonResponse({"response": "No regular program found in session."})
            else:
                return JsonResponse({"response": "Please respond with 'yes' or 'no' to clarify."})

        center_keywords = [
            "center",
            "centre",
            "regional center",
            "study center",
            "cneters",
            "centres",
            "cenrets",
        ]
        program_keywords = [
            "program",
            "course",
            "study",
            "list programs",
            "show programs",
            "progams",
            "courses",
        ]

        lsc_keywords = [
            "lsc",
            "learning support center",
            "study center",
            "lscs",
            "learning support centers",
        ]
        category_keywords = ["category", "field", "discipline", "stream", "branch", "type", "area"]
        regional_center_query_match = re.search(
            r"lsc(?:'s)? under regional center (\w+)", normalized_query
        )

        if regional_center_query_match:
            regional_center_name = regional_center_query_match.group(1)
            print(
                f">>> LSC query for specific regional center detected: {regional_center_name}"
            )
            lsc_data = fetch_lsc_data(regional_center_name)
            if lsc_data:
                lsc_list_html = f"Here are the LSCs under {regional_center_name} Regional Center:\n<ol>"
                for lsc in lsc_data:
                    rc_id = lsc.get("lscrc")
                    # Ensure rc_id is an integer for mapping lookup
                    if isinstance(rc_id, str) and rc_id.isdigit():
                        rc_id = int(rc_id)
                    elif not isinstance(rc_id, int):
                        rc_id = None  # Set to None if not a valid ID

                    rc_name = rc_name_mapping.get(rc_id, "N/A")  # Use the mapping
                    print(
                        f"DEBUG: LSC RC ID: {lsc.get('lscrc')}, Processed RC ID: {rc_id}, RC Name from mapping: {rc_name}"
                    )
                    lsc_list_html += f"<li><strong>{lsc['lscname']}</strong><br>Address: {lsc['lscaddress']}<br>Contact: {lsc['lscnumber']}<br>Coordinator: {lsc['coordinatorname']}<br>Email: <a href='mailto:{lsc['coordinatormail']}' style='color: #0066cc;'>{lsc['coordinatormail']}</a><br>RC: {rc_id}<br>RCNAME: {lscrc['rcname']}</li>"
                lsc_list_html += "</ol>"
                return JsonResponse({"message": lsc_list_html})
            else:
                return JsonResponse(
                    {"message": "Sorry, I couldn't fetch LSC data at the moment."}
                )
        elif any(keyword in normalized_query for keyword in lsc_keywords):
            print(">>> General LSC query detected, fetching all LSCs...")
            lsc_data = fetch_lsc_data()
            if lsc_data:
                all_lscs_html = "Here are the Learning Support Centers:\n<ol>"
                for lsc in lsc_data:
                    rc_id = lsc.get("lscrc")
                    # Ensure rc_id is an integer for mapping lookup
                    if isinstance(rc_id, str) and rc_id.isdigit():
                        rc_id = int(rc_id)
                    elif not isinstance(rc_id, int):
                        rc_id = None  # Set to None if not a valid ID

                    rc_name = rc_name_mapping.get(rc_id, "N/A")  # Use the mapping
                    print(
                        f"DEBUG: LSC RC ID: {lsc.get('lscrc')}, Processed RC ID: {rc_id}, RC Name from mapping: {rc_name}"
                    )
                    all_lscs_html += f"<li><strong>{lsc['lscname']}</strong><br>Address: {lsc['lscaddress']}<br>Contact: {lsc['lscnumber']}<br>Coordinator: {lsc['coordinatorname']}<br>Email: <a href='mailto:{lsc['coordinatormail']}' style='color: #0066cc;'>{lsc['coordinatormail']}</a><br>RC: {rc_id}<br>RCNAME: {rc_name}</li>"
                all_lscs_html += "</ol>"
                return JsonResponse({"message": all_lscs_html})
            else:
                return JsonResponse(
                    {"message": "Sorry, I couldn't fetch LSC data at the moment."}
                )
        elif any(keyword in normalized_query for keyword in center_keywords):
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
                    centers_html = (
                        "Here are our regional centers:\n<ol>"
                        + "".join([f"<li>{center}</li>" for center in centers])
                        + "</ol>"
                    )
                    return JsonResponse({"message": centers_html})
                else:
                    return JsonResponse({"message": "No centers found."})
            else:
                print(f">>> Centers fetch failed: {centers_response.content}")
                return centers_response  # Return error response from fetch_centers
        elif any(keyword in normalized_query for keyword in category_keywords):
            print(">>> Category query detected.")
            # Extract category from user_query
            category_name = ""
            category_match = re.search(r"programs? (?:in|under|for)?\s*([a-zA-Z0-9\s]+)", normalized_query)
            if category_match:
                extracted_category = category_match.group(1).strip()
                # Simple mapping for common abbreviations
                if extracted_category.lower() == "ug":
                    category_name = "Undergraduate"
                elif extracted_category.lower() == "pg":
                    category_name = "Postgraduate"
                else:
                    category_name = extracted_category
            
            if not category_name:
                return JsonResponse({"message": "Please specify a category, e.g., 'programs in Arts' or 'show me programs for Science'."})

            # Fetch all programs
            university_response = requests.get(
                UNIVERSITY_API_URL, headers=university_headers, timeout=10
            )

            if university_response.status_code != 200:
                return JsonResponse(
                    {"message": "Sorry, unable to fetch university data now."}
                )

            uni_data = university_response.json()
            all_programs = uni_data.get("programme", [])

            # Filter programs by category
            print(f"DEBUG: Filtering for category: {category_name.lower()}")
            for program in all_programs:
                print(f"DEBUG: Program name: {program.get('pgm_name')}, Category: {program.get('pgm_category')}")
            filtered_programs = [
                p for p in all_programs if p.get('pgm_category', '').lower() == category_name.lower()
            ]

            if filtered_programs:
                request.session['programs'] = filtered_programs
                program_list_html = f"The programs we offer under {category_name.capitalize()} category are:\n<ol>"
                for i, program in enumerate(filtered_programs):
                    program_list_html += f"<li>{program.get('pgm_name', 'N/A')}</li>"
                program_list_html += "</ol>"
                program_list_html += "<p>If you would like to know about a specific program, type the corresponding number.</p>"
                return JsonResponse({"message": program_list_html})
            else:
                return JsonResponse({"message": f"No programs found in the {category_name.capitalize()} category."})

        elif any(keyword in normalized_query for keyword in program_keywords):
            university_response = requests.get(
                UNIVERSITY_API_URL, headers=university_headers, timeout=10
            )

            print(f">>> University API status: {university_response.status_code}")
            print(
                f">>> University API response (preview): {university_response.text[:200]}"
            )

            if university_response.status_code != 200:
                return JsonResponse(
                    {"message": "Sorry, unable to fetch university data now."}
                )

            uni_data = university_response.json()
            programs = uni_data.get("programme", [])
            print(f"DEBUG: Programs data from API: {programs[:2]}") # Print first 2 programs for brevity
            if not isinstance(programs, list):
                return JsonResponse(
                    {"message": "Invalid data format received from university API."}
                )

            # Store programs in session for later retrieval
            request.session['programs'] = programs

            program_list_html = "Here are the programs offered:\n<ol>"
            for i, program in enumerate(programs):
                program_list_html += f"<li>{program.get('pgm_name', 'N/A')}</li>"
            program_list_html += "</ol>"
            program_list_html += "<p>If you would like to know about a specific program, type the corresponding number.</p>"

            return JsonResponse({"message": program_list_html})
        # Handle specific program queries
        elif len(normalized_query) > 3: # Avoid very short queries for specific programs
            print(f">>> Specific program query detected: {normalized_query}")
            university_response = requests.get(
                UNIVERSITY_API_URL, headers=university_headers, timeout=10
            )

            if university_response.status_code != 200:
                return JsonResponse(
                    {"message": "Sorry, unable to fetch university data now."}
                )

            uni_data = university_response.json()
            all_programs = uni_data.get("programme", [])

            matching_programs = []
            for program in all_programs:
                pgm_name = program.get('pgm_name', '').lower()
                if normalized_query in pgm_name:
                    matching_programs.append(program)
            
            if len(matching_programs) > 1:
                # Check if one is 'Honours' and the other is not
                honours_program = None
                regular_program = None
                for program in matching_programs:
                    if 'honours' in program.get('pgm_name', '').lower():
                        honours_program = program
                    else:
                        regular_program = program
                
                if honours_program and regular_program:
                    print(f">>> Multiple program matches found. Requesting clarification for: {regular_program.get('pgm_name', 'N/A')}")
                    request.session['clarification_needed'] = True
                    request.session['honours_program'] = honours_program
                    request.session['regular_program'] = regular_program
                    return JsonResponse({"message": f"Are you asking about the Honours version of {regular_program.get('pgm_name', 'N/A')}? Please reply with 'yes' or 'no'."})
                elif len(matching_programs) == 1:
                    found_program = matching_programs[0]
            elif len(matching_programs) == 1:
                found_program = matching_programs[0]
            else:
                found_program = None

            if found_program:
                print(f">>> Program found: {found_program.get('pgm_name', 'N/A')}")
                program_details_html = f"<h3>{found_program.get('pgm_name', 'N/A')}</h3>"
                program_details_html += f"<p><strong>Program Code:</strong> {found_program.get('pgm_code', 'N/A')}</p>"
                program_details_html += f"<p><strong>Category:</strong> {found_program.get('pgm_category', 'N/A')}</p>"
                program_details_html += f"<p><strong>Duration:</strong> {found_program.get('pgm_duration', 'N/A')}</p>"
                program_details_html += f"<p><strong>Description:</strong> {found_program.get('pgm_desc', 'N/A')}</p>"
                # Add more fields as needed based on your API response structure
                return JsonResponse({"message": program_details_html})
        elif user_query.isdigit():
            stored_programs = request.session.get('programs')

            # Only process as a program number if programs are actually stored in the session
            if stored_programs and len(stored_programs) > 0:
                program_index = int(user_query) - 1
                if 0 <= program_index < len(stored_programs):
                    program = stored_programs[program_index]
                    print(f"DEBUG: Retrieved program details from session: {program}")
                    program_details_html = f"<p><b>Program Name:</b> {program.get('pgm_name', 'N/A')}</p>"
                    program_details_html += f"<p><b>Description:</b> {program.get('pgm_desc', 'N/A')}</p>"
                    program_details_html += f"<p><b>Category:</b> {program.get('pgm_category', 'N/A')}</p>"
                    program_details_html += f"<p><b>Year:</b> {program.get('pgm_year', 'N/A')}</p>"
                    return JsonResponse({"message": program_details_html})
                else:
                    # If index is out of range, clear programs from session and return an error message
                    if 'programs' in request.session:
                        del request.session['programs']
                    return JsonResponse({"message": "The number you entered does not correspond to an available program. Please list programs first or enter a valid program number."})
            else:
                # If no programs are stored in session, clear any stale 'programs' key and return an error message
                if 'programs' in request.session:
                    del request.session['programs']
                return JsonResponse({"message": "Please list programs first before entering a number."})
        # This 'else' block handles all non-digit queries
        else:
            # If no specific keyword is detected, proceed with general query processing
            university_response = requests.get(
                UNIVERSITY_API_URL, headers=university_headers, timeout=10
            )

            print(f">>> University API status: {university_response.status_code}")
            print(
                f">>> University API response (preview): {university_response.text[:200]}"
            )

            if university_response.status_code != 200:
                return JsonResponse(
                    {"message": "Sorry, unable to fetch university data now."}
                )

            uni_data = university_response.json()
            programs = uni_data.get("programme", [])
            print(f"DEBUG: Programs data from API: {programs[:2]}") # Print first 2 programs for brevity
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


def fetch_lsc_data(regional_center_name=None):
    """
    Fetches LSC data from the API.
    Optionally filters by regional center name.
    """
    global LSC_API_URL, UNIVERSITY_API_KEY  # Declare global to ensure access
    try:
        print(f">>> Fetching LSC data for regional center: {regional_center_name}")
        lsc_headers = {
            "X-API-KEY": UNIVERSITY_API_KEY,
            "Accept": "application/json",
        }
        params = {}
        if regional_center_name:
            params["regional_center"] = (
                regional_center_name  # Assuming 'regional_center' is the parameter name
            )
        response = requests.get(
            LSC_API_URL, headers=lsc_headers, params=params, timeout=10
        )

        print(f">>> LSC API Response Status: {response.status_code}")
        print(
            f">>> LSC API Response Content: {response.text[:500]}"
        )  # Log first 500 characters of response
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
        lsc_data = response.json()

        if regional_center_name:
            # Filter LSCs by regional center name
            filtered_lscs = [
                rc
                for rc in lsc_data.get("lsc", [])
                if rc.get("lscname").lower() == regional_center_name.lower()
            ]
            return filtered_lscs
        else:
            # TODO: Ensure the LSC API returns the full regional center object (including 'rcname') within 'lscrc'
            # if 'lscrc' is a foreign key. If not, a separate API call to fetch regional center details
            # based on 'lscrc' ID would be necessary here.
            lsc_list = lsc_data.get("lsc", [])
            for lsc in lsc_list:
                print(
                    f"DEBUG in fetch_lsc_data: LSC Name: {lsc.get('lscname')}, LSC RC ID (raw): {lsc.get('lscrc')}"
                )
            return lsc_list
    except requests.exceptions.RequestException as e:
        print(f"Error fetching LSC data: {e}")
        return None


def build_prompt(user_query, programs, centers=None):
    # Only include program list if user explicitly asks about programs
    program_text = ""
    if any(
        keyword in user_query.lower()
        for keyword in ["program", "course", "study", "list programs", "show programs"]
    ):
        # Format programs as HTML ordered list
        program_html_items = []
        for program in programs:
            program_name = program.get("pgm_name", "Unknown")
            program_html_items.append(f"<li>{program_name}</li>")

        program_text = f"Here are our available programs:\n<ol>{''.join(program_html_items)}</ol>\n\n"

    centers_text = ""
    # Always include centers_text if centers data is available
    if centers:
        # Format centers as HTML ordered list
        centers_html_items = []
        for center in centers:
            centers_html_items.append(f"<li>{center}</li>")

        centers_text = f"Here are our regional centers:\n<ol>{''.join(centers_html_items)}</ol>\n\n"

    prompt = (
        "You are an expert assistant for SGOU (Sri Guru Gobind Singh Tricentenary University). "
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
        "When listing centers, follow these rules strictly:\n"
        "1. Format as HTML ordered list using <ol> and <li> tags\n"
        "2. Each center must be in its own <li> tag\n"
        "3. Include all center information with proper HTML formatting\n"
        "4. Use <br> tags for line breaks within each center's information\n"
        f"{program_text}"
        f"{centers_text}"
        f"User question: {user_query}\n"
        "Format your response appropriately - use paragraphs for general information and HTML ordered lists for both programs and centers. "
        "Avoid asking follow-up questions that require a 'yes' or 'no' response. Provide direct and complete answers to user queries."
        "Do not include phrases like 'We offer a wide range of academic programs. If you would like to know more about our programs, here is a list of our programs:' unless the user explicitly asks for programs."
        "Always be accurate and helpful. If you're not certain about specific details, direct users to the official website for the most up-to-date information."
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
            "content": "You are a helpful assistant for SGOU. When asked about the duration of a program, respond ONLY with the duration in years (e.g., '3 years' or '4 years'). Do not mention the university name unnecessarily. If the user asks about a program, list all the programs available in that category. If the user asks about a center, list all the centers available in that category. Always prioritize accuracy and provide helpful, complete responses.",
        },
        {"role": "user", "content": prompt},
    ]

    if centers_data:
        messages.append(
            {
                "role": "system",
                "content": f"Here are our regional centers: {centers_data}",
            }
        )

    # INCREASED max_tokens for better center display
    body = {
        "model": "llama3-70b-8192",
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 1500,  # Increased from 500 to 1500
    }

    try:
        response = requests.post(
            GROQ_API_URL, headers=headers, json=body, timeout=30
        )  # Increased timeout
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

# Rest of your existing functions remain the same...
def fetch_centers(request):
    try:
        headers = {
            "X-API-KEY": UNIVERSITY_API_KEY,
            "Accept": "application/json",
        }

        response = requests.get(CENTERS_API_URL, headers=headers, timeout=10)

        response.raise_for_status()
        raw_centers_content = response.text

        # Debug: Print the raw API response content
        print(
            f">>> Raw centers API response content: {raw_centers_content[:500]} (truncated to 500 chars)"
        )

        centers_data = {}
        try:
            centers_data = json.loads(raw_centers_content)
        except json.JSONDecodeError:
            print(
                f"Error: Could not decode JSON from centers API response. Content: {raw_centers_content}"
            )
            return []  # Return empty list if JSON decoding fails

        centers_list = []
        if isinstance(centers_data, dict):
            # Try different possible keys for centers data
            centers_list = (
                centers_data.get("rc", [])
                or centers_data.get("centers", [])
                or centers_data.get("data", [])
            )
        elif isinstance(centers_data, list):
            centers_list = centers_data

        print(f"Debug: centers_list before processing in fetch_centers: {centers_list}")

        # Ensure each item in centers_list is a dictionary
        processed_centers_list = []
        for item in centers_list:
            print(f"Debug: Processing item type: {type(item)}, content: {item}")
            if isinstance(item, str):
                try:
                    # Attempt to decode string-encoded JSON
                    decoded_item = json.loads(item)
                    if isinstance(decoded_item, dict):
                        processed_centers_list.append(decoded_item)
                    else:
                        print(
                            f"Warning: Decoded item is not a dictionary: {decoded_item}"
                        )
                except json.JSONDecodeError:
                    print(f"Warning: Could not decode string item to JSON: {item}")
            elif isinstance(item, dict):
                processed_centers_list.append(item)
            else:
                print(
                    f"Warning: Unexpected item type in centers_list: {type(item)} - {item}"
                )

        formatted_centers = []
        for idx, center in enumerate(processed_centers_list):
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
        return JsonResponse({"formatted_centers": formatted_centers, "raw_centers": processed_centers_list}) # Return both formatted and raw data

    except requests.exceptions.RequestException as e:
        print(f">>> Error fetching centers: {e}")
        return JsonResponse(
            {"message": "Sorry, unable to fetch center data now."}, status=500
        )
    except ValueError as e:
        print(f">>> Error parsing centers JSON: {e}")
        return JsonResponse(
            {"message": "Sorry, invalid center data received."}, status=500
        )
    except Exception as e:
        print(f">>> An unexpected error occurred: {e}")
        return JsonResponse(
            {"message": "An unexpected error occurred while fetching centers."},
            status=500,
        )


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
