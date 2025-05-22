import requests

def query_local_llm(prompt):
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "gemma3",
                "prompt": prompt,
                "stream": False
            },
            timeout=20
        )
        reply = response.json()['response']
        print("[LLM RESPONSE]", reply)  # ✅ This confirms it's LLM output
        return reply
    except Exception as e:
        print("LLM Error:", e)
        return None
