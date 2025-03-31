import requests
import json
from datetime import datetime

def test_location_endpoint():
    url = "http://127.0.0.1:8000/location"
    
    # Test data
    data = {
        "_type": "location",
        "lat": 34.0522,
        "lon": -118.2437,
        "tst": int(datetime.now().timestamp()),  # Current timestamp
        "tid": "device1"
    }
    
    headers = {"Content-Type": "application/json"}
    
    try:
        print("Sending location data:", json.dumps(data, indent=2))
        response = requests.post(url, json=data, headers=headers)
        
        print("\nResponse Status:", response.status_code)
        print("Response Body:", json.dumps(response.json(), indent=2))
        
        # Test get last location
        last_location_url = f"{url.replace('/location', '/last-location')}?tid={data['tid']}"
        get_response = requests.get(last_location_url)
        print("\nLast Location Response:", json.dumps(get_response.json(), indent=2))
        
    except requests.exceptions.RequestException as e:
        print(f"Error occurred: {e}")

if __name__ == "__main__":
    test_location_endpoint() 