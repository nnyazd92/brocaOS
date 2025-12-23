BrocaOS Starter Kit

This starter kit helps you run a local BrocaAPI for development and for building a hosted MVP. It includes Dockerfile, docker-compose for local dev, OpenAPI spec, a minimal Python SDK stub, and a Helm chart skeleton.

Quickstart (5 minutes):
1. Ensure Docker & docker-compose are installed.
2. From repo root: docker-compose -f starter_kit/docker-compose.yml up --build
3. The API is available at http://localhost:8080 (health endpoint: /health)
4. See starter_kit/sdk/python/examples/quickstart.py for example usage of the SDK stub.

Example curl:
- Health: curl http://localhost:8080/health
- Create session: curl -X POST http://localhost:8080/session -H 'Content-Type: application/json' -d '{"user_id":"user-1"}'
- Upsert memory: curl -X POST http://localhost:8080/memory/upsert -H 'Content-Type: application/json' -d '{"session_id":"<SESSION_ID>","items":[{"id":"m1","text":"likes green","meta":{}}]}'
- Query memory: curl -X POST http://localhost:8080/memory/query -H 'Content-Type: application/json' -d '{"session_id":"<SESSION_ID>","query":"green","top":5}'

Notes:
- The app uses an in-memory store; data will be lost when the container restarts.
- For production, replace in-memory stores with Postgres/Vector DB and secure actuator approvals.

License: Apache-2.0 (see starter_kit/LICENSE)
