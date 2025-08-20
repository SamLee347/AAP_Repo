import requests
import json

# Simple test for category prediction
url = "http://localhost:5000/categorization"
data = {"item_id": 104}

print(f"Testing category prediction for item {data['item_id']}...")
print(f"Making request to: {url}")

try:
    response = requests.post(url, json=data)
    print(f"Response status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print("SUCCESS!")
        print(f"Category: {result.get('category', 'N/A')}")
        print(f"Confidence: {result.get('confidence', 'N/A')}")
        print(f"Complete response: {json.dumps(result, indent=2)}")
    else:
        print(f"ERROR: {response.status_code}")
        print(f"Response text: {response.text}")
        
except Exception as e:
    print(f"Exception occurred: {e}")
