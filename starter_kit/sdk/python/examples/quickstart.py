#!/usr/bin/env python3
"""FastAPI starter_kit quickstart example.

This script demonstrates calling the starter API /health and creating a session.
Run after the docker-compose stack is up and the API is reachable at http://localhost:8080
"""

import requests
import time

API_URL = "http://localhost:8080"


def wait_for_health(timeout=60):
    start = time.time()
    while True:
        try:
            r = requests.get(f"{API_URL}/health", timeout=3)
            if r.status_code == 200:
                print("API healthy:", r.text)
                return True
        except Exception as e:
            print("Waiting for API...", e)
        if time.time() - start > timeout:
            print("Timeout waiting for API")
            return False
        time.sleep(2)


def create_session(user_id="example_user"):
    payload = {"user_id": user_id}
    r = requests.post(f"{API_URL}/session", json=payload, timeout=5)
    r.raise_for_status()
    print("Created session:", r.json())
    return r.json()


if __name__ == '__main__':
    if wait_for_health():
        create_session()
