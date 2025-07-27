"""
Langfuse APIエラーをデバッグ
"""
import httpx
import os
import base64
from dotenv import load_dotenv

load_dotenv()

def test_api_error():
    """APIエラーの詳細を確認"""
    
    public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    secret_key = os.getenv("LANGFUSE_SECRET_KEY")
    host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
    
    print(f"Host: {host}")
    print(f"Public Key: {public_key[:10]}..." if public_key else "Public Key: None")
    print(f"Secret Key: {'***' if secret_key else 'None'}")
    
    # Basic認証ヘッダーを作成
    auth_string = f"{public_key}:{secret_key}"
    auth_header = f"Basic {base64.b64encode(auth_string.encode()).decode()}"
    
    session_id = "9a261480-c414-4f4a-bb36-2fa72dd70918"
    
    # 1. トレースAPIを試す
    print("\n=== Traces API ===")
    url = f"{host}/api/public/traces"
    params = {"sessionId": session_id}
    
    response = httpx.get(
        url,
        params=params,
        headers={
            "Authorization": auth_header,
            "Content-Type": "application/json"
        }
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code != 200:
        print(f"Error: {response.text}")
    else:
        data = response.json()
        traces = data.get("data", [])
        print(f"Found {len(traces)} traces")
        
        if traces:
            # 最初のトレースでobservationsを試す
            trace_id = traces[0]["id"]
            print(f"\nFirst trace ID: {trace_id}")
            
            # 2. Observations by traceId
            print("\n=== Observations by traceId ===")
            url = f"{host}/api/public/observations"
            params = {"traceId": trace_id}
            
            response = httpx.get(
                url,
                params=params,
                headers={
                    "Authorization": auth_header,
                    "Content-Type": "application/json"
                }
            )
            
            print(f"Status: {response.status_code}")
            if response.status_code != 200:
                print(f"Error: {response.text}")
    
    # 3. Observations by sessionId
    print("\n=== Observations by sessionId ===")
    url = f"{host}/api/public/observations"
    params = {"sessionId": session_id}
    
    response = httpx.get(
        url,
        params=params,
        headers={
            "Authorization": auth_header,
            "Content-Type": "application/json"
        }
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code != 200:
        print(f"Error: {response.text}")
        print(f"\nHeaders sent: {response.request.headers}")
        print(f"URL: {response.request.url}")


if __name__ == "__main__":
    test_api_error()