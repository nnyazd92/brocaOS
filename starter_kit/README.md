BrocaOS Starter Kit

This starter kit helps you run a local BrocaAPI for development and for building a hosted MVP. It includes Dockerfile, docker-compose for local dev, OpenAPI spec, a minimal Python SDK stub, and a Helm chart skeleton.

Quickstart (5 minutes):
1. Ensure Docker & docker-compose are installed.
2. From repo root: docker-compose -f starter_kit/docker-compose.yml up --build
3. The API is available at http://localhost:8080 (health endpoint: /health)
4. See starter_kit/sdk/python/examples/quickstart.py for example usage of the SDK stub.

License: Apache-2.0 (see starter_kit/LICENSE)
