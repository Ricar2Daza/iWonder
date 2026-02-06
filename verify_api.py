import httpx
import sys

def check_health():
    try:
        response = httpx.get("http://127.0.0.1:8000/")
        if response.status_code == 200:
            print("✅ API Root (Health Check): OK")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ API Root Failed: Status {response.status_code}")
            sys.exit(1)
            
        response_docs = httpx.get("http://127.0.0.1:8000/docs")
        if response_docs.status_code == 200:
            print("✅ API Docs (Swagger): OK")
        else:
            print(f"❌ API Docs Failed: Status {response_docs.status_code}")

    except Exception as e:
        print(f"❌ Connection Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    check_health()
