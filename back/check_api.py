
import urllib.request
import json
import sys

base_url = "http://localhost:8000/api/v1"
username = "User"

def check_endpoint(endpoint):
    url = f"{base_url}{endpoint}"
    print(f"Checking {url}...")
    try:
        with urllib.request.urlopen(url) as response:
            print(f"Status Code: {response.getcode()}")
            data = response.read()
            try:
                json_data = json.loads(data)
                print("JSON Response (truncated):")
                print(str(json_data)[:200])
            except:
                print("Raw Response:")
                print(data.decode('utf-8'))
    except urllib.error.HTTPError as e:
        print(f"HTTP Error: {e.code}")
        print(e.read().decode('utf-8'))
    except Exception as e:
        print(f"Error: {e}")

check_endpoint(f"/users/{username}")
print("-" * 20)
check_endpoint(f"/users/{username}/answers")
