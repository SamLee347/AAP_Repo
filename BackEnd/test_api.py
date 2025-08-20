import requests
import json

def test_categorization():
    url = "http://127.0.0.1:5000/categorization"
    data = {"item_id": 102}
    
    try:
        print(f"Testing API: {url}")
        print(f"Request data: {data}")
        
        response = requests.post(url, json=data, timeout=10)
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Category: {result.get('category', 'N/A')}")
            print(f"Confidence: {result.get('confidence', 'N/A')}")
            print(f"Attributes: {result.get('attributes', [])}")
        else:
            print(f"Error: {response.status_code} - {response.text}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_categorization()
