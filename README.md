# PetuAI

**Adaptive Image Intelligence for developers.**

PetuAI is an open developer platform for AI-assisted image editing with a controlled continual-learning feedback loop. Version 0.1 provides the API contract, authentication, image-processing backend interface, feedback collection, model-version registry, tests, and Docker deployment.

> PetuAI v0.1 does **not** claim to be a newly trained foundation model. The generative backend is pluggable so an approved diffusion/image-editing model can be connected and later fine-tuned from validated feedback.

## Features

- FastAPI REST API
- API-key authentication
- `/v1/edit`, `/v1/enhance`, `/v1/feedback`, `/v1/models`
- Pluggable image-editing backend
- Controlled feedback collection for continual learning
- Model registry/versioning foundation
- Docker-ready deployment
- Owner-only administrative endpoints

## Quick start

```bash
cp .env.example .env
docker compose up --build
```

Open `http://localhost:8000/docs`.

## Authentication

Set `PETUAI_API_KEY` for developer calls and `PETUAI_OWNER_KEY` for owner-only administration. Never commit real keys.

## Continual learning design

Feedback is recorded but never trains the production model directly. A future training worker can select consented/validated examples, train an adapter, run regression benchmarks, and promote a candidate only after evaluation.

## Project status

**v0.1.0 — developer preview.** The default `LocalEnhanceBackend` provides deterministic enhancement so the API works without a GPU. Connect a generative backend in `app/engine.py` for instruction-driven semantic editing.

## Ownership & administration

PetuAI supports one application-level owner secret (`PETUAI_OWNER_KEY`). No endpoint exists to create additional owners/admins. GitHub repository ownership and collaborators remain governed by GitHub account settings.

## License

Apache-2.0. See `LICENSE`.
