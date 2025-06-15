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
QNA_API_URL = os.getenv("QNA_API_URL")
GROQ_API_URL = os.getenv("GROQ_API_URL")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
SGOU_OFFICIAL_WEBSITE = "https://sgou.ac.in"


def index(request):
    return render(request, "index.html")


def enhanced_keyword_matching(user_query, api_question):
    """
    Enhanced keyword matching that checks for common words and phrases
    """
    user_words = set(user_query.lower().split())
    api_words = set(api_question.lower().split())
    
    # Calculate word overlap
    common_words = user_words.intersection(api_words)
    word_overlap_ratio = len(common_words) / max(len(user_words), len(api_words))
    
    # Check for key phrases
    user_lower = user_query.lower()
    api_lower = api_question.lower()
    
    # Common question patterns
    question_patterns = [
        "what is", "what are", "how to", "when is", "when are", "where is", "where are",
        "full form", "meaning of", "definition of", "eligibility", "admission", "fee",
        "duration", "course", "program", "certificate", "degree", "how long"
    ]
    
    pattern_matches = 0
    for pattern in question_patterns:
        if pattern in user_lower and pattern in api_lower:
            pattern_matches += 1
    
    # Boost score if patterns match
    if pattern_matches > 0:
        word_overlap_ratio += 0.2 * pattern_matches
    
    return word_overlap_ratio


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
        
        # Define headers for API calls early
        university_headers = {
            "X-API-KEY": UNIVERSITY_API_KEY,
            "Accept": "application/json",
        }
        
        # Normalize user query for keyword detection to handle typos
        normalized_query = user_query.lower()
        
        # Define keywords for different query types
        center_keywords = [
            "center", "centre", "regional center", "study center", 
            "cneters", "centres", "cenrets",
        ]
        program_keywords = [
            "program", "course", "study", "list programs", "show programs", 
            "progams", "courses", "program name",
        ]
        lsc_keywords = [
            "lsc", "learning support center", "study center", 
            "lscs", "learning support centers",
        ]
        category_keywords = [
            "category", "field", "discipline", "stream", "branch", "type", "area", 
            "ug", "pg", "stp", "four year", "short term", "post graduate", 
            "under graduate", "degree"
        ]
        
        # Check if this is a program or category related query first
        is_program_query = any(keyword in normalized_query for keyword in program_keywords)
        is_category_query = any(keyword in normalized_query for keyword in category_keywords)
        is_center_query = any(keyword in normalized_query for keyword in center_keywords)
        is_lsc_query = any(keyword in normalized_query for keyword in lsc_keywords) or re.search(r"lsc(?:'s)? under regional center ([\w\s]+)", normalized_query)

        fee_keywords = ["fee structure", "fees", "admission fee", "tuition fee", "cost of program"]
        is_fee_query = any(keyword in normalized_query for keyword in fee_keywords)
        
        # Check field queries
        field_keywords = ['category', 'year', 'years', 'duration', 'description', 'desc', 'details','long']
        is_field_query = any(keyword in normalized_query for keyword in field_keywords) and ('of' in normalized_query or 'for' in normalized_query)

        # If this is a field query for a program, handle it first
        if is_field_query:
            print(f">>> Field query detected: {normalized_query}")
            try:
                print(f">>> Attempting to connect to University API: {UNIVERSITY_API_URL}")
                university_response = requests.get(UNIVERSITY_API_URL, headers=university_headers, timeout=15)
                print(f">>> University API status: {university_response.status_code}")
                
                if university_response.status_code == 200:
                    uni_data = university_response.json()
                    all_programs = uni_data.get("programme", [])
                    print(f">>> Retrieved {len(all_programs)} programs from API")
                    
                    if not all_programs:
                        print(">>> Warning: No programs returned from API")
                        return JsonResponse({"message": "Sorry, no program data is currently available. Please try again later."})
                    
                    field_response = handle_specific_program_field_query(user_query, all_programs)
                    print(f">>> Field response: {field_response}")
                    
                    if field_response:
                        return JsonResponse({"message": field_response})
                    else:
                        print(">>> No field response returned")
                        return JsonResponse({"message": f"Sorry, I couldn't find information about that specific field for the program. Please try a different query."})
                else:
                    print(f">>> University API error: Status {university_response.status_code}, Response: {university_response.text[:200]}")
                    return JsonResponse({"message": f"Sorry, there was an issue connecting to the university database (Status: {university_response.status_code}). Please try again later."})
            except requests.exceptions.ConnectionError as e:
                print(f">>> Connection error to University API: {str(e)}")
                return JsonResponse({"message": "Sorry, unable to connect to the university database. Please check your internet connection and try again later."})
            except requests.exceptions.Timeout as e:
                print(f">>> Timeout error to University API: {str(e)}")
                return JsonResponse({"message": "Sorry, the connection to the university database timed out. Please try again later."})
            except Exception as e:
                print(f">>> Error in field query handling: {str(e)}")
                return JsonResponse({"message": "Sorry, there was an unexpected error processing your request. Please try again later."})

        # Combined fee structure handling
        if is_fee_query or request.session.get('waiting_for_fee_program'):
            program_name_to_query = None

            # Case 1: User is responding to a previous prompt for program name
            if request.session.get('waiting_for_fee_program'):
                program_name_to_query = user_query.strip()
                del request.session['waiting_for_fee_program'] # Clear the flag
                print(f">>> Handling fee query response for program: {program_name_to_query}")
            # Case 2: Initial fee query, try to extract program name from current query
            elif is_fee_query:
                match = re.search(r"(?:fee structure|fees|cost)\s+(?:for|of)\s+([\w\s]+)", normalized_query)
                if match:
                    program_name_to_query = match.group(1).strip()
                print(f">>> Handling initial fee query. Extracted program: {program_name_to_query}")

            if program_name_to_query:
                query_for_api = f"fee structure for {program_name_to_query}"
                print(f">>> Querying questioners API for fee structure: {query_for_api}")
                try:
                    api_url = QNA_API_URL
                    headers = {"X-API-KEY": UNIVERSITY_API_KEY}
                    response = requests.get(api_url, headers=headers, params={'query': query_for_api}, timeout=10)
                    response.raise_for_status()
                    questions_data = response.json()
                    
                    best_match = None
                    best_similarity = 0
                    questions_list = questions_data.get('question', [])

                    for item in questions_list:
                        if "question" in item and "answer" in item:
                            api_question = item["question"]
                            api_answer = item["answer"]
                            
                            combined_similarity = (SequenceMatcher(None, query_for_api.lower(), api_question.lower()).ratio() * 0.4) + \
                                                  (enhanced_keyword_matching(query_for_api, api_question) * 0.6)
                            
                            if combined_similarity > best_similarity:
                                best_match = {"question": api_question, "answer": api_answer, "similarity": combined_similarity}
                                best_similarity = combined_similarity
                    
                    if best_match and best_similarity > 0.7: # Use a similar threshold as general QNA
                        return JsonResponse({"message": best_match["answer"]}, status=200)
                    else:
                        return JsonResponse({"message": f"Sorry, I couldn't find the fee structure for '{program_name_to_query}'. Please try rephrasing or check the program name."})

                except requests.exceptions.RequestException as e:
                    print(f">>> Error fetching fee structure from questioners API: {e}")
                    return JsonResponse({"message": "Sorry, I'm having trouble fetching fee information right now. Please try again later."})
            else:
                # If no program name was found and it was an initial fee query, prompt for program name
                request.session['waiting_for_fee_program'] = True
                return JsonResponse({"message": "Which program's fee structure do you want to know? Please tell me the program name."})
            return JsonResponse({}) # Ensure a response is always returned from this block

        # IMPROVED: Check questioners API for ALL non-specific queries (not just non-program/category/center/LSC)"(?:fee structure|fees|cost)\s+(?:for|of)\s+([\w\s]+)", normalized_query)
            if match:
                program_name_match = match.group(1).strip()
            
            if program_name_match:
                query_for_api = f"fee structure for {program_name_match}"
                print(f">>> Querying questioners API for fee structure: {query_for_api}")
                try:
                    api_url = QNA_API_URL
                    headers = {"X-API-KEY": UNIVERSITY_API_KEY}
                    response = requests.get(api_url, headers=headers, params={'query': query_for_api}, timeout=10)
                    response.raise_for_status()
                    questions_data = response.json()
                    
                    best_match = None
                    best_similarity = 0
                    questions_list = questions_data.get('question', [])

                    for item in questions_list:
                        if "question" in item and "answer" in item:
                            api_question = item["question"]
                            api_answer = item["answer"]
                            
                            combined_similarity = (SequenceMatcher(None, query_for_api.lower(), api_question.lower()).ratio() * 0.4) + \
                                                  (enhanced_keyword_matching(query_for_api, api_question) * 0.6)
                            
                            if combined_similarity > best_similarity:
                                best_match = {"question": api_question, "answer": api_answer, "similarity": combined_similarity}
                                best_similarity = combined_similarity
                    
                    if best_match and best_similarity > 0.7: # Use a similar threshold as general QNA
                        return JsonResponse({"message": best_match["answer"]}, status=200)
                    else:
                        return JsonResponse({"message": f"Sorry, I couldn't find the fee structure for '{program_name_match}'. Please try rephrasing or check the program name."})

                except requests.exceptions.RequestException as e:
                    print(f">>> Error fetching fee structure from questioners API: {e}")
                    return JsonResponse({"message": "Sorry, I'm having trouble fetching fee information right now. Please try again later."})
            else:
                request.session['waiting_for_fee_program'] = True
                return JsonResponse({"message": "Which program's fee structure do you want to know? Please tell me the program name."})

        # IMPROVED: Check questioners API for ALL non-specific queries (not just non-program/category/center/LSC)
        # Only skip API check for very specific structural queries like "list all programs" or "show all centers"
        skip_api_check = (
            (is_program_query and any(word in normalized_query for word in ["list", "show", "all"])) or
            (is_center_query and any(word in normalized_query for word in ["list", "show", "all"])) or
            (is_lsc_query and any(word in normalized_query for word in ["list", "show", "all"]))
        )
        
        if not skip_api_check:
            try:
                api_url = QNA_API_URL
                print(f">>> Checking questioners API for query: {user_query}")
                # Add Authorization header with API key
                headers = {
                    "X-API-KEY": UNIVERSITY_API_KEY  # Replace with your actual API key
                }
                response = requests.get(api_url, headers=headers, timeout=10)
                response.raise_for_status()
                questions_data = response.json()
                print(f">>> Questions data structure: {type(questions_data)}")
                
                best_match = None
                best_similarity = 0
                
                questions_list = questions_data.get('question', [])
                print(f">>> Found {len(questions_list)} questions in API")
                
                for item in questions_list:
                    if "question" in item and "answer" in item:
                        api_question = item["question"]
                        api_answer = item["answer"]
                        
                        # Check for exact match first (highest priority)
                        if user_query.lower().strip() == api_question.lower().strip():
                            print(f">>> EXACT MATCH found: {api_question}")
                            return JsonResponse({"answer": api_answer}, status=200)
                        
                        # Enhanced similarity calculation
                        sequence_similarity = SequenceMatcher(None, user_query.lower(), api_question.lower()).ratio()
                        keyword_similarity = enhanced_keyword_matching(user_query, api_question)
                        
                        # Combined similarity score (giving more weight to keyword matching)
                        combined_similarity = (sequence_similarity * 0.4) + (keyword_similarity * 0.6)
                        
                        print(f">>> Comparing:")
                        print(f"    User: '{user_query}'")
                        print(f"    API:  '{api_question}'")
                        print(f"    Sequence: {sequence_similarity:.3f}, Keyword: {keyword_similarity:.3f}, Combined: {combined_similarity:.3f}")
                        
                        if combined_similarity > best_similarity:
                            best_match = {"question": api_question, "answer": api_answer, "similarity": combined_similarity}
                            best_similarity = combined_similarity
                
                # LOWERED threshold for better matching
                similarity_threshold = 0.7  # Increased for stricter matching
                
                if best_match and best_similarity > similarity_threshold:
                    print(f">>> BEST MATCH found (score: {best_similarity:.3f}): {best_match['question']}")
                    print(f">>> Returning answer: {best_match['answer'][:100]}...")
                    return JsonResponse({"answer": best_match["answer"]}, status=200)
                else:
                    print(f">>> No good match found. Best similarity: {best_similarity:.3f}")
                
            except requests.exceptions.Timeout:
                print(">>> Questioners API timeout - continuing with normal processing")
            except requests.exceptions.RequestException as e:
                print(f">>> Error checking questioners API: {e} - continuing with normal processing")
            except Exception as e:
                print(f">>> Unexpected error with questioners API: {e} - continuing with normal processing")

        # Fetch all regional centers once
        rc_name_mapping = {}
        try:
            centers_response = fetch_centers(request)
            if centers_response.status_code == 200:
                centers_data = json.loads(centers_response.content)
                print(f"Debug: centers_data in process_query: {centers_data}")
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
                        # Normalize rc_name to handle special characters like '–', '\xa0', and Unicode replacement character
                        rc_name = rc_name.replace('–', '-').replace('\xa0', ' ').replace('\ufffd', '-').strip()
                        rc_name_mapping[rc_id] = rc_name
        except Exception as e:
            print(f"Error fetching regional centers for mapping: {e}")

        try:
            regional_center_query_match = re.search(
                r"lsc(?:'s)? under (.*)", normalized_query, re.IGNORECASE
            )

            if regional_center_query_match:
                regional_center_name_raw = regional_center_query_match.group(1).strip()
                
                # Extract the actual regional center name from the raw query
                if regional_center_name_raw.lower().startswith("regional centre – "):
                    regional_center_name = regional_center_name_raw[len("regional centre – "):].strip()
                elif regional_center_name_raw.lower().startswith("regional center "):
                    regional_center_name = regional_center_name_raw[len("regional center "):].strip()
                else:
                    regional_center_name = regional_center_name_raw

                # Normalize regional_center_name to handle special characters like '–' and '\xa0'
                regional_center_name = regional_center_name.replace('–', '-').replace('\xa0', ' ').strip()

                print(f"Debug: Extracted and normalized regional_center_name: '{regional_center_name}'")
                print(f"Debug: rc_name_mapping content: {rc_name_mapping}")

                lsc_data = fetch_lsc_data(regional_center_name, rc_name_mapping)
                if lsc_data:
                    lsc_dropdown_html = f"Here are the Learning Support Centers under {regional_center_name.title()} Regional Center:<br><br>"
                    for lsc in lsc_data:
                        rc_id = lsc.get("lscrc")
                        if isinstance(rc_id, str) and rc_id.isdigit():
                            rc_id = int(rc_id)
                        elif not isinstance(rc_id, int):
                            rc_id = None

                        rc_name = rc_name_mapping.get(rc_id, "N/A")

                        lsc_name = lsc.get("lscname", "N/A").replace("'", "&apos;")
                        lsc_address = lsc.get("lscaddress", "N/A").replace("'", "&apos;")
                        lsc_number = lsc.get("lscnumber", "N/A")
                        lsc_coordinator = lsc.get("coordinatorname", "N/A").replace("'", "&apos;")
                        lsc_email = lsc.get("coordinatormail", "N/A")

                        lsc_dropdown_html += f'''
                    <div class="lsc-item" style="border-radius:8px;">
                    <div class="lsc-header" onclick="toggleDropdown(this)" style="cursor:pointer; display:flex; justify-content:space-between; font-weight:bold; color:#0066cc;">
                        <span>{lsc_name}</span>
                        <span class="lsc-arrow">&#9660;</span>
                    </div>
                    <div class="lsc-details" style="display:none; margin-top:8px;">
                        <strong>Address:</strong> {lsc_address}<br>
                        <strong>Contact:</strong> {lsc_number}<br>
                        <strong>Coordinator:</strong> {lsc_coordinator}<br>
                        <strong>Email:</strong> <a href="mailto:{lsc_email}" style="color:#0066cc;">{lsc_email}</a><br>
                        <strong>RC ID:</strong> {rc_id}<br>
                        <strong>RC Name:</strong> {rc_name}
                    </div>
                    </div>
                    '''
                    return JsonResponse({"message": lsc_dropdown_html})


            elif any(keyword in normalized_query for keyword in center_keywords):
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
                lsc_data = fetch_lsc_data(rc_name_mapping=rc_name_mapping)
                if lsc_data:
                    all_lscs_html = "Here are our Learning Support Centers:<br><br>"
                    for lsc in lsc_data:
                        rc_id = lsc.get("lscrc")
                        if isinstance(rc_id, str) and rc_id.isdigit():
                            rc_id = int(rc_id)
                        elif not isinstance(rc_id, int):
                            rc_id = None

                        rc_name = rc_name_mapping.get(rc_id, "N/A")

                        # 🧠 Safe encoding to prevent HTML errors
                        lsc_name = lsc.get("lscname", "N/A").replace("'", "&apos;")
                        lsc_address = lsc.get("lscaddress", "N/A").replace("'", "&apos;")
                        lsc_number = lsc.get("lscnumber", "N/A")
                        lsc_coordinator = lsc.get("coordinatorname", "N/A").replace("'", "&apos;")
                        lsc_email = lsc.get("coordinatormail", "N/A")

                        all_lscs_html += f'''
            <div class="lsc-item" style="border-radius:8px; ">
            <div class="lsc-header" onclick="toggleDropdown(this)" style="cursor:pointer; display:flex; justify-content:space-between; font-weight:bold; color:#0066cc;">
                <span>{lsc_name}</span>
                <span class="lsc-arrow">&#9660;</span>
            </div>
            <div class="lsc-details" style="display:none; margin-top:8px;">
                <strong>Address:</strong> {lsc_address}<br>
                <strong>Contact:</strong> {lsc_number}<br>
                <strong>Coordinator:</strong> {lsc_coordinator}<br>
                <strong>Email:</strong> <a href="mailto:{lsc_email}" style="color:#0066cc;">{lsc_email}</a><br>
                <strong>RC ID:</strong> {rc_id}<br>
                <strong>RC Name:</strong> {rc_name}
            </div>
            </div>
            '''
                    return JsonResponse({"message": all_lscs_html})
                else:
                    return JsonResponse({"message": "Sorry, I couldn't fetch LSC data at the moment."})

        except Exception as e:
            print(f"Error in LSC/Center processing: {e}")

        # Handle queries asking for the number of programs
        if any(word in normalized_query for word in ["how many programs", "number of programs", "total programs", "programs count"]):
            try:
                university_response = requests.get(UNIVERSITY_API_URL, headers=university_headers, timeout=10)
                university_response.raise_for_status()
                all_programs = university_response.json().get("programme", [])
                num_programs = len(all_programs)
                return JsonResponse({"message": f"We have {num_programs} programs available."})
            except requests.exceptions.RequestException as e:
                print(f">>> Error fetching program count: {e}")
                return JsonResponse({"message": "Sorry, I couldn't fetch the number of programs at the moment. Please try again later."})

        # Program and category handling
        if is_program_query and is_category_query:
            print(">>> Detected query for programs within a category")
            print(f"DEBUG: Original query: '{normalized_query}'")
            print(f"DEBUG: is_program_query: {is_program_query}")
            print(f"DEBUG: is_category_query: {is_category_query}")
            
            category_alias_map = {
                "fyug": "FYUG",
                "fyugp": "FYUG",
                "four year": "FYUG",
                "honour": "FYUG",
                "honours": "FYUG",
                "short term": "STP",
                "shortterm": "STP",
                "short term program": "STP",
                "short term programs": "STP",
                "short term programmes": "STP",
                "stp": "STP",
                "ugp": "UG",
                "ug": "UG",
                "pg": "PG",
                "post graduate": "PG",
                "postgrad": "PG",
                "postgraduates": "PG",
                "under graduates": "UG"
            }

            matched_category = None
            for key in sorted(category_alias_map.keys(), key=len, reverse=True):
                if key in normalized_query:
                    matched_category = category_alias_map[key]
                    print(f"DEBUG: Matched '{key}' -> {matched_category}")
                    break

            if not matched_category:
                return JsonResponse({"message": "Please mention a valid category like UG, PG, FYUG, or STP."})

            university_response = requests.get(UNIVERSITY_API_URL, headers=university_headers, timeout=10)
            if university_response.status_code != 200:
                return JsonResponse({"message": "Sorry, unable to fetch university data now."})

            all_programs = university_response.json().get("programme", [])

            categories_found = set()
            category_counts = {}
            for p in all_programs:
                cat = p.get('pgm_category', '').strip()
                if cat:
                    categories_found.add(cat)
                    category_counts[cat] = category_counts.get(cat, 0) + 1

            print(f"DEBUG: Categories found in program data: {sorted(categories_found)}")
            print(f"DEBUG: Category counts: {category_counts}")
            print(f"DEBUG: Looking for matched category: '{matched_category}'")
            
            if matched_category == "STP":
                print("DEBUG: Special STP debugging:")
                stp_like_categories = []
                for cat in categories_found:
                    if "stp" in cat.lower() or "short" in cat.lower() or "term" in cat.lower() or "programme" in cat.lower():
                        stp_like_categories.append(cat)
                print(f"DEBUG: STP-like categories found: {stp_like_categories}")
                
                potential_stp_programs = []
                for p in all_programs:
                    pgm_name = p.get('pgm_name', '').lower()
                    pgm_cat = p.get('pgm_category', '').lower()
                    if any(word in pgm_name or word in pgm_cat for word in ['certificate', 'short', 'term', 'skill']):
                        potential_stp_programs.append(p)
                print(f"DEBUG: Found {len(potential_stp_programs)} potential STP programs")
                if potential_stp_programs:
                    for i, prog in enumerate(potential_stp_programs[:3]):
                        print(f"DEBUG: STP candidate {i+1}: {prog.get('pgm_name')} — Category: '{prog.get('pgm_category')}'")

            print(f"DEBUG: About to start filtering...")

            filtered_programs = []
            
            # Method 1: Exact case match
            for p in all_programs:
                if p.get('pgm_category', '').strip() == matched_category:
                    filtered_programs.append(p)
            
            print(f"DEBUG: Exact match found: {len(filtered_programs)} programs")
            
            # Method 2: Case insensitive match if exact failed
            if not filtered_programs:
                for p in all_programs:
                    if p.get('pgm_category', '').strip().upper() == matched_category.upper():
                        filtered_programs.append(p)
                print(f"DEBUG: Case insensitive match found: {len(filtered_programs)} programs")
            
            # Method 3: Partial matching if still no results
            if not filtered_programs:
                for p in all_programs:
                    cat = p.get('pgm_category', '').strip().upper()
                    if matched_category.upper() in cat:
                        filtered_programs.append(p)
                print(f"DEBUG: Partial match found: {len(filtered_programs)} programs")

            print(f"DEBUG: Matched Category: {matched_category}")
            print(f"DEBUG: Total filtered programs: {len(filtered_programs)}")
            
            for i, prog in enumerate(filtered_programs[:5]):
                print(f"DEBUG: {i+1}. {prog.get('pgm_name')} — Category: '{prog.get('pgm_category')}'")

            if filtered_programs:
                request.session['programs'] = filtered_programs
                program_list_html = f"Programs under {matched_category} category:<ol>"
                for prog in filtered_programs:
                    program_list_html += f"<li>{prog.get('pgm_name', 'N/A')}</li>"
                program_list_html += "</ol><p>You can reply with a number to know more about a specific program.</p>"
                return JsonResponse({"message": program_list_html})
            else:
                available_categories = ", ".join(sorted(categories_found))
                return JsonResponse({
                    "message": f"No programs found under '{matched_category}' category. Available categories are: {available_categories}"
                })

        elif any(keyword in normalized_query for keyword in program_keywords):
            university_response = requests.get(UNIVERSITY_API_URL, headers=university_headers, timeout=10)

            print(f">>> University API status: {university_response.status_code}")
            print(f">>> University API response (preview): {university_response.text[:200]}")

            if university_response.status_code != 200:
                return JsonResponse({"message": "Sorry, unable to fetch university data now."})

            uni_data = university_response.json()
            programs = uni_data.get("programme", [])
            print(f"DEBUG: Programs data from API: {programs[:2]}")
            if not isinstance(programs, list):
                return JsonResponse({"message": "Invalid data format received from university API."})

            request.session['programs'] = programs

            program_list_html = "Here are the programs offered:\n<ol>"
            for i, program in enumerate(programs):
                program_list_html += f"<li>{program.get('pgm_name', 'N/A')}</li>"
            program_list_html += "</ol>"
            program_list_html += "<p>If you would like to know about a specific program, type the corresponding number.</p>"

            return JsonResponse({"message": program_list_html})

        # Handle general specific program queries
        elif len(normalized_query) > 3:
            print(f">>> Specific program query detected: {normalized_query}")
            
            try:
                university_response = requests.get(UNIVERSITY_API_URL, headers=university_headers, timeout=15)
                
                if university_response.status_code != 200:
                    return JsonResponse({"message": "Sorry, unable to fetch university data now."})

                uni_data = university_response.json()
                all_programs = uni_data.get("programme", [])
                
                if not all_programs:
                    return JsonResponse({"message": "Sorry, no program data is currently available. Please try again later."})
            except Exception as e:
                print(f">>> ERROR in process_query: {str(e)}")
                return JsonResponse({"message": "There was an error processing your request."})

            matching_programs = []
            similarity_threshold = 0.6

            for program in all_programs:
                pgm_name = program.get('pgm_name', '').lower()
                similarity = SequenceMatcher(None, normalized_query, pgm_name).ratio()
                
                if similarity >= similarity_threshold:
                    matching_programs.append((program, similarity))
            
            matching_programs.sort(key=lambda x: x[1], reverse=True)
            matching_programs = [p[0] for p in matching_programs]

            query_program_type = None
            for p_type in ['ba', 'ma', 'b.sc', 'm.sc', 'b.com', 'm.com', 'phd']:
                if normalized_query.startswith(p_type):
                    query_program_type = p_type
                    break

            filtered_by_type_programs = []
            if query_program_type:
                for program in matching_programs:
                    pgm_name_lower = program.get('pgm_name', '').lower()
                    if pgm_name_lower.startswith(query_program_type):
                        filtered_by_type_programs.append(program)
            
            programs_to_display = filtered_by_type_programs if filtered_by_type_programs else matching_programs

            if len(programs_to_display) > 1:
                request.session['programs'] = programs_to_display
                program_list_html = "Multiple programs found. Please specify by number:\n<ol>"
                for i, program in enumerate(programs_to_display):
                    program_list_html += f"<li>{program.get('pgm_name', 'N/A')} ({program.get('pgm_category', 'N/A')})</li>"
                program_list_html += "</ol>"
                return JsonResponse({"message": program_list_html})
            else:
                found_program = matching_programs[0] if matching_programs else None

            if found_program:
                print(f">>> Program found (direct query): {found_program.get('pgm_name', 'N/A')}")
                print(f"DEBUG: found_program pgm_year: {found_program.get('pgm_year')}, duration: {found_program.get('duration')}")
                program_details_html = f"<h3>{found_program.get('pgm_name', 'N/A')}</h3>"
                program_details_html += f"<p><strong>Description:</strong> {found_program.get('pgm_desc', 'N/A')}</p>"
                program_details_html += f"<p><strong>Category:</strong> {found_program.get('pgm_category', 'N/A')}</p>"
                program_details_html += f"<p><strong>year:</strong> {found_program.get('pgm_year', 'N/A')}</p>"
                return JsonResponse({"message": program_details_html})
                
        elif user_query.isdigit():
            stored_programs = request.session.get('programs')

            if stored_programs and len(stored_programs) > 0:
                program_index = int(user_query) - 1
                if 0 <= program_index < len(stored_programs):
                    program = stored_programs[program_index]
                    print(f"DEBUG: Retrieved program details from session (by number): {program.get('pgm_name', 'N/A')}")
                    print(f"DEBUG: session program pgm_year: {program.get('pgm_year')}, duration: {program.get('duration')}")
                    program_details_html = f"<p><b>Program Name:</b> {program.get('pgm_name', 'N/A')}</p>"
                    program_details_html += f"<p><b>Description:</b> {program.get('pgm_desc', 'N/A')}</p>"
                    program_details_html += f"<p><b>Category:</b> {program.get('pgm_category', 'N/A')}</p>"
                    program_details_html += f"<p><strong>year:</strong> {program.get('pgm_year', 'N/A')}</p>"
                    return JsonResponse({"message": program_details_html})
                else:
                    if 'programs' in request.session:
                        del request.session['programs']
                    return JsonResponse({"message": "The number you entered does not correspond to an available program. Please list programs first or enter a valid program number."})
            else:
                if 'programs' in request.session:
                    del request.session['programs']
                return JsonResponse({"message": "Please list programs first before entering a number."})
        else:
            # Default processing with Groq API
            centers = []
            programs = []
            
            university_response = requests.get(UNIVERSITY_API_URL, headers=university_headers, timeout=10)

            print(f">>> University API status: {university_response.status_code}")
            print(f">>> University API response (preview): {university_response.text[:200]}")

            if university_response.status_code != 200:
                return JsonResponse({"message": "Sorry, unable to fetch university data now."})

            uni_data = university_response.json()
            programs = uni_data.get("programme", [])
            print(f"DEBUG: Programs data from API: {programs[:2]}")
            if not isinstance(programs, list):
                return JsonResponse({"message": "Invalid data format received from university API."})

            prompt = build_prompt(user_query, programs, centers)
            answer = call_groq_api(prompt, programs, centers)

            return JsonResponse({"message": answer})

    except json.JSONDecodeError:
        print(">>> ERROR: Invalid JSON in request body")
        return JsonResponse({"message": "Invalid request format."})
    except Exception as e:
        print(f">>> ERROR in process_query: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({"message": "There was an error processing your request. Please try again later."})
    
    # Default return if no other condition is met
    return JsonResponse({"message": "I'm sorry, I couldn't understand your request. Please try rephrasing it."})


def fetch_lsc_data(regional_center_name=None, rc_name_mapping=None):
    """
    Fetches LSC data and optionally filters by regional center name.
    Also formats LSCs in dropdown format for RC-specific queries.
    """
    api_url = LSC_API_URL
    headers = {"X-API-KEY": UNIVERSITY_API_KEY}
    
    try:
        response = requests.get(api_url, headers=headers, timeout=10)
        response.raise_for_status()
        lsc_data = response.json().get("lsc", [])

        if regional_center_name and rc_name_mapping:
            target_rc_id = None
            regional_center_name = regional_center_name.strip().lower()

            for rc_id, rc_name in rc_name_mapping.items():
                cleaned = rc_name.replace('–', '-').replace('—', '-').replace('\xa0', ' ')
                if '-' in cleaned:
                    after_dash = cleaned.split('-')[-1].strip().lower()
                else:
                    after_dash = cleaned.strip().lower()

                print(f"Checking user input '{regional_center_name}' against trimmed RC part '{after_dash}'")
                if regional_center_name == after_dash:
                    target_rc_id = rc_id
                    break

            if target_rc_id is None:
                print(f"No regional center matches '{regional_center_name}' after trimming")
                return []

            filtered_lscs = []
            for lsc in lsc_data:
                lsc_rc_id = lsc.get("lscrc")
                if isinstance(lsc_rc_id, str) and lsc_rc_id.isdigit():
                    lsc_rc_id = int(lsc_rc_id)
                if lsc_rc_id == target_rc_id:
                    filtered_lscs.append(lsc)
            return filtered_lscs

        else:
            return lsc_data
    except requests.exceptions.RequestException as e:
        print(f"Error fetching LSC data: {e}")
        return None



def handle_specific_program_field_query(user_query, all_programs):
    """
    Handle queries asking for specific fields of specific programs
    e.g., "category of MA History", "duration of BA English", etc.
    """
    normalized_query = user_query.lower()

    # Define field keywords and their corresponding API fields
    field_mapping = {
        'category': 'pgm_category',
        'year': 'pgm_year', 
        'years': 'pgm_year',
        'duration': 'pgm_year',
        'description': 'pgm_desc',
        'desc': 'pgm_desc',
        'details': 'pgm_desc',
        'fee structure': 'pgm_fee',
        'fees': 'pgm_fee',
    }

    # Check if query contains field keywords
    detected_field = None
    api_field = None
    for field_keyword, api_field_name in field_mapping.items():
        if field_keyword in normalized_query:
            detected_field = field_keyword
            api_field = api_field_name
            break
    
    if not detected_field:
        return None
    
    # Extract program name from query - be more specific
    query_for_program = normalized_query
    # Remove the field keyword and connecting words more carefully
    for field_kw in field_mapping.keys():
        # Replace field keyword with space to avoid merging words
        query_for_program = query_for_program.replace(field_kw, ' ')
    # Replace connecting words with spaces
    query_for_program = query_for_program.replace(' of ', ' ').replace(' for ', ' ').replace(' the ', ' ')
    # Clean up extra spaces and trim
    query_for_program = ' '.join(query_for_program.split()).strip()
    
    print(f"DEBUG: Looking for program: '{query_for_program}'")
    
    # Find matching program with appropriate similarity threshold for field queries
    best_match = None
    best_similarity = 0
    similarity_threshold = 0.6  # Lowered threshold to better match program names
    
    for program in all_programs:
        pgm_name = program.get('pgm_name', '').lower()
        similarity = SequenceMatcher(None, query_for_program, pgm_name).ratio()
        
        print(f"DEBUG: Comparing '{query_for_program}' with '{pgm_name}' - Similarity: {similarity}")
        
        if similarity >= similarity_threshold and similarity > best_similarity:
            best_match = program
            best_similarity = similarity
    
    if not best_match:
        return f"Sorry, I couldn't find a program matching '{query_for_program}'. Please be more specific with the program name."
    
    program_name = best_match.get('pgm_name', 'N/A')
    field_value = best_match.get(api_field, 'N/A')
    
    print(f"DEBUG: Found program: {program_name}, Field: {detected_field}, Value: {field_value}")
    
    # Format response based on field type
    if detected_field in ['category']:
        return f"The category of <strong>{program_name}</strong> is: <strong>{field_value}</strong>"
    elif detected_field in ['year', 'years', 'duration']:
        return f"The duration of <strong>{program_name}</strong> is: <strong>{field_value}</strong>"
    elif detected_field in ['description', 'desc', 'details']:
        # Check if field_value is empty or N/A
        if field_value == 'N/A' or not field_value:
            return f"<strong>Description of {program_name}:</strong><br><br>Sorry, no description is available for this program."
        return f"<strong>Description of {program_name}:</strong><br><br>{field_value}"
    else:
        return f"<strong>{detected_field.title()} of {program_name}:</strong> {field_value}"


def handle_fee_structure_query(program_data):
    """
    Handles queries specifically asking for fee structure.
    """
    pgm_name = program_data.get('pgm_name')
    pgm_fee = program_data.get('pgm_fee')

    if pgm_fee:
        return f"The fee structure for {pgm_name} is: {pgm_fee}"
    else:
        return f"Sorry, I couldn't find the fee structure for {pgm_name}."


def build_prompt(user_query, programs, centers=None):
    print(f"DEBUG: Programs received by build_prompt: {programs}")
    # Only include program list if user explicitly asks about programs
    program_text = ""
    normalized_query = user_query.lower()
    program_html_items = []
    print(f"DEBUG: Programs data type: {type(programs)}")
    print(f"DEBUG: Programs sample: {programs[:2] if programs else 'None'}")

    # Check for category-specific program queries
    category_keywords = ["ug", "pg", "diploma", "certificate", "doctoral", "post graduate", "under graduate"]
    category_mapping = {
        "ug": "undergraduate",
        "under graduate": "undergraduate",
        "pg": "postgraduate",
        "post graduate": "postgraduate"
    }
    
    found_category = None
    for cat_kw in category_keywords:
        if cat_kw in normalized_query and ("program" in normalized_query or "category" in normalized_query):
            found_category = cat_kw
            break

    if found_category:
        # Map abbreviated categories to their full names
        search_category = category_mapping.get(found_category.lower(), found_category.lower())
        print(f"DEBUG: Searching for category: {found_category} mapped to {search_category}")
        filtered_programs = [p for p in programs if p.get("pgm_category", "").lower() == search_category]
        if filtered_programs:   
            for program in filtered_programs:
                print(f"DEBUG: Program category: {program.get('pgm_category')}")
                print(f"DEBUG: Program full data: {program}")
                program_name = program.get("pgm_name", "Unknown")
                program_html_items.append(f"<li>{program_name}</li>")
            program_text = f"Here are our {found_category.upper()} programs:\n<ol>{''.join(program_html_items)}</ol>\n\n"
        else:
            program_text = f"No {found_category.upper()} programs found.\n\n"
    elif any(
        keyword in normalized_query
        for keyword in ["program", "course", "study", "list programs", "show programs", "all programs", "what are the programs"]
    ):
        # Format all programs as HTML ordered list
        for program in programs:
            print(f"DEBUG: All Program category: {program.get('pgm_category')}")
            program_name = program.get("pgm_name", "Unknown")
            program_html_items.append(f"<li>{program_name}</li>")
        program_text = f"Here are all our available programs:\n<ol>{''.join(program_html_items)}</ol>\n\n"

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
                center_html = f"""
<div class="rc-item">
  <div class="rc-header" onclick="toggleDropdown(this)">
    <span class="rc-title">{name}</span>
    <span class="rc-arrow">&#9660;</span>
  </div>
  <div class="rc-details" style="display: none; margin-top: 5px;">
    <strong>Address:</strong> {address}<br>
    <strong>RC Director:</strong> {headname}<br>
    <strong>Number:</strong> {headnumber}<br>
    <strong>Email:</strong> <a href='mailto:{headmail}' style='color: #0066cc;'>{headmail}</a>
  </div>
</div>
"""

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
                                "description": program.get("pgm_desc"),                                "category": program.get("pgm_category"),
                                "pgm_year": program.get("pgm_year"),
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
        print(f"DEBUG: Programs data type: {type(programs)}")
        print(f"DEBUG: Programs sample: {programs[:2] if programs else 'None'}")
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