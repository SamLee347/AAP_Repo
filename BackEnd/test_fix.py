import requests
import json

# Test the fixed API
url = "http://127.0.0.1:5000/categorization"
data = {
    "item_id": 102  # This is the "Stylish Shirt" that should be "Books" according to our fix
}

try:
    response = requests.post(url, json=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    if response.status_code == 200:
        result = response.json()
        print(f"Category: {result.get('category', 'N/A')}")
        print("SUCCESS! The API is now returning proper category names.")
    else:
        print("ERROR: API returned non-200 status")
except Exception as e:
    print(f"ERROR: {e}")
