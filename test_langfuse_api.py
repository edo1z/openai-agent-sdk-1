"""
Langfuse APIの最適な方法を調査
"""
import httpx
import os
import base64
from dotenv import load_dotenv

load_dotenv()

class LangfuseAPITester:
    def __init__(self):
        self.public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
        self.secret_key = os.getenv("LANGFUSE_SECRET_KEY")
        self.host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
        
        auth_string = f"{self.public_key}:{self.secret_key}"
        self.auth_header = f"Basic {base64.b64encode(auth_string.encode()).decode()}"
    
    def test_sessions_api(self, session_id: str):
        """Sessions APIを試す"""
        print("\n=== Sessions API ===")
        url = f"{self.host}/api/public/sessions/{session_id}"
        
        response = httpx.get(
            url,
            headers={
                "Authorization": self.auth_header,
                "Content-Type": "application/json"
            }
        )
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Keys: {list(data.keys())}")
            return data
        else:
            print(f"Error: {response.text}")
            return None
    
    def test_observations_with_session(self, session_id: str):
        """SessionIdでobservationsを直接取得"""
        print("\n=== Observations by SessionId ===")
        url = f"{self.host}/api/public/observations"
        
        params = {
            "sessionId": session_id,
            "limit": 100
        }
        
        response = httpx.get(
            url,
            params=params,
            headers={
                "Authorization": self.auth_header,
                "Content-Type": "application/json"
            }
        )
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            observations = data.get("data", [])
            print(f"Observations数: {len(observations)}")
            
            # 最初のobservationの構造を確認
            if observations:
                first = observations[0]
                print(f"\n最初のobservation:")
                print(f"  Type: {first.get('type')}")
                print(f"  Name: {first.get('name')}")
                print(f"  Input exists: {'input' in first}")
                print(f"  Output exists: {'output' in first}")
            
            return observations
        else:
            print(f"Error: {response.text}")
            return []


if __name__ == "__main__":
    session_id = input("テストするセッションIDを入力: ").strip()
    if not session_id:
        session_id = "02c71b00-ea74-4621-92bf-96b5dea89625"
    
    tester = LangfuseAPITester()
    
    # Sessions APIを試す
    session_data = tester.test_sessions_api(session_id)
    
    # Observations APIを試す
    observations = tester.test_observations_with_session(session_id)