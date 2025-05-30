import requests
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
import os

UNIVERSITY_API_URL = "http://sgou.ac.in/api/programmes"
UNIVERSITY_API_KEY = "$2y$10$M0JLrgVmX2AUUqMZkrqaKOrgaMMaVFusOVjiXkVjc1YLyqcYFY9Bi"
VECTOR_STORE_DIR = os.path.join(os.path.dirname(__file__), 'vector_store')

def fetch_data():
    university_headers = {
        "X-API-KEY": UNIVERSITY_API_KEY,
        "Accept": "application/json",
    }
    try:
        response = requests.get(UNIVERSITY_API_URL, headers=university_headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        programs = data.get('programme', [])
        return programs
    except requests.RequestException as e:
        print(f"Error fetching data from university API: {e}")
        return []

def generate_embeddings():
    programs = fetch_data()
    if not programs:
        print("No programs to generate embeddings for.")
        return

    texts = [p.get('pgm_name', '') + " " + p.get('pgm_desc', '') for p in programs]
    embeddings = OpenAIEmbeddings()
    vector_store = FAISS.from_texts(texts, embeddings)
    vector_store.save_local(VECTOR_STORE_DIR)
    print("Vector DB updated successfully.")