Starter Kit Quickstart

1. docker-compose -f docker-compose.yml up --build
2. Wait until Postgres and MinIO are ready, then start BrocaAPI.
3. Use the Python SDK example to create a session and upsert/query memory.

Troubleshooting:
- If ports conflict, update docker-compose.yml ports.
- Check logs with: docker-compose logs -f
