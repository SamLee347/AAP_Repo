import requests
import json

# Test the category prediction API
url = "http://localhost:5000/predict_category"
data = {"item_id": 101}

try:
    response = requests.post(url, json=data)
    if response.status_code == 200:
        result = response.json()
        print("Category Prediction Result:")
        print(f"Category: {result['category']}")
        print(f"Confidence: {result['confidence']:.1f}%")
        print("\nAttributes:")
        for attr in result['attributes']:
            print(f"• {attr}")
        print(f"\nStock: {result['stock']} units")
        print(f"Total Orders: {result['total_orders']}")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
except Exception as e:
    print(f"Error making request: {e}")
