import requests
import json

def test_guest_chat():
    url = "http://127.0.0.1:8001/api/chat/ask"
    payload = {"question": "How do I register my National ID?"}
    
    print(f"Testing Guest Access to: {url}")
    try:
        response = requests.post(url, json=payload)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("Response Data:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            if data.get("id") == 0:
                print("SUCCESS: User identified as guest (ID 0)")
            else:
                print("WARNING: Unexpected ID for guest")
        else:
            print(f"FAILED: {response.text}")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    test_guest_chat()
