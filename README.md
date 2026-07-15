# EduCore

Modular SaaS Education ERP for CBC, 8-4-4, British, TVET, and University
institutions — built Kenya-first, extensible globally.

## Design Documentation

The full architecture — modular monolith rationale, Django app boundaries,
React architecture, database design, API contract, authentication,
permissions, multi-tenancy, and deployment — is in [`docs/`](docs/). Read
`docs/architecture.md` first.

The implementation roadmap (dependency-ordered phases) is tracked outside
this repo as an approved execution plan; `docs/` reflects the target design
each phase builds toward.

## Local Development

```
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
cp docker/.env.example docker/.env
docker compose -f docker/docker-compose.yml -f docker/docker-compose.dev.yml --env-file docker/.env up --build
```

- Backend: http://localhost:8000 (Django admin at `/admin/`, API at `/api/v1/`, docs at `/api/docs/`)
- Frontend: http://localhost:5173
- MinIO console: http://localhost:9001

## Production / Staging

```
docker compose -f docker/docker-compose.yml -f docker/docker-compose.prod.yml --env-file docker/.env up -d --build
```

See `docs/deployment.md` for the full topology, edge/TLS setup, backup
strategy, and dedicated-infra tenant provisioning.
