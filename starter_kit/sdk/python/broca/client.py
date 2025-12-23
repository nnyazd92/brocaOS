import requests

class BrocaClient:
    def __init__(self, endpoint="http://localhost:8080", api_key=None):
        self.endpoint = endpoint.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()
        if api_key:
            self.session.headers.update({"Authorization": f"Bearer {api_key}"})

    def health(self):
        return self.session.get(f"{self.endpoint}/health").json()

    def create_session(self, user_id: str):
        r = self.session.post(f"{self.endpoint}/session", json={"user_id": user_id})
        return r.json()

    def memory_query(self, session_id: str, query: str, top: int = 5):
        r = self.session.post(f"{self.endpoint}/memory/query", json={"session_id": session_id, "query": query, "top": top})
        return r.json()

    def memory_upsert(self, session_id: str, items):
        r = self.session.post(f"{self.endpoint}/memory/upsert", json={"session_id": session_id, "items": items})
        return r.json()

    def actuator_request(self, session_id: str, action: str, payload: dict):
        r = self.session.post(f"{self.endpoint}/actuator/request", json={"session_id": session_id, "action": action, "payload": payload})
        return r.json()

    def actuator_approve(self, request_id: str, approver: str):
        r = self.session.post(f"{self.endpoint}/actuator/approve", json={"request_id": request_id, "approver": approver})
        return r.json()
