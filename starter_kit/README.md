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


## Monetizable BrocaAPI starter

This starter now includes:

- **API-key authentication** for all mutating/query endpoints (`x-api-key` header).
- **Accounts / API keys / usage_events** tables in Postgres for basic metering.
- A small admin bootstrap script to create an account + API key:

  ```bash
  DATABASE_URL=postgresql://postgres:postgres@localhost:5432/broca \\n  python -m starter_kit.app.admin_init
  ```

  This prints a raw API key once; use it in requests as:

  ```bash
  curl -H "x-api-key: <YOUR_API_KEY>" http://localhost:8080/health
  ```

With this you can run a single-tenant, dev-focused BrocaAPI and start treating:

- `/session` as a **billable session primitive**.
- `/memory/upsert` and `/memory/query` as **billable memory operations**.
- `/actuator/*` as **governed action hooks** for higher-value plans.

See `starter_kit/docs/quickstart.md` for more details.
