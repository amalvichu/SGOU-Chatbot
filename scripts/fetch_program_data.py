import requests
import json

api_url = 'http://192.168.20.2:8000/api/programmes'
api_key = '$2y$10$M0JLrgVmX2AUUqMZkrqaKOrgaMMaVFusOVjiXkVjc1YLyqcYFY9Bi'

headers = {
    'X-API-KEY': api_key
}

response = requests.get(api_url, headers=headers)

if response.status_code == 200:
    data = response.json()
    with open('Chatbot/scripts/programs.json', 'w') as f:
        json.dump(data['programme'], f, indent=2)
    print("✅ Data saved successfully.")
else:
    print("❌ Failed to fetch:", response.status_code)
