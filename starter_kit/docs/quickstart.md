Starter Kit Quickstart

1. docker-compose -f docker-compose.yml up --build
2. Wait until Postgres and MinIO are ready, then start BrocaAPI.
3. Use the Python SDK example to create a session and upsert/query memory.

Troubleshooting:
- If ports conflict, update docker-compose.yml ports.
- Check logs with: docker-compose logs -f


## Authentication and API keys

The starter now requires an API key for all mutating and query endpoints.

1. Ensure your database is running (via docker-compose).
2. From the repo root, run:

   ```bash
   DATABASE_URL=postgresql://postgres:postgres@localhost:5432/broca \
   python -m starter_kit.app.admin_init
   ```

   This will:
   - Create a default account (name: `wizard`, configurable via `BROCA_STARTER_ACCOUNT_NAME`).
   - Generate an API key and print it once.

3. Use the printed key in requests as an `x-api-key` header, for example:

   ```bash
   curl -H "x-api-key: <YOUR_API_KEY>" http://localhost:8080/health

   curl -H "x-api-key: <YOUR_API_KEY>"         -H 'Content-Type: application/json'         -X POST http://localhost:8080/session         -d '{"user_id":"user-1"}'
   ```

Endpoints protected by API key:
- `POST /session`
- `POST /memory/upsert`
- `POST /memory/query`
- `POST /actuator/request`
- `POST /actuator/approve`

`GET /health` and `GET /` are public.
