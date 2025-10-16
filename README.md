---
title: Tds Project 1 Deployment
emoji: 🌖
colorFrom: yellow
colorTo: gray
sdk: docker
pinned: false
license: mit
---

# Tds Project 1

Lightweight service that accepts a task payload, generates or updates a GitHub Pages website using an LLM-backed code generator, and reports back an evaluation callback. It includes simple mock evaluators for local testing.

> [!note]
> This repository contains code that depends on external API keys (GitHub, OpenAI). Keep secrets out of source control and never share them publicly.

## Quick links
- App entry: [`app.handle_task`](app.py) — [app.py](app.py)  
- Core actions: [`actions.write_code`](actions.py), [`actions.create_github_repo`](actions.py), [`actions.push_files`](actions.py), [`actions.enable_github_pages`](actions.py), [`actions.get_latest_sha`](actions.py), [`actions.send_evaluation_response`](actions.py) — [actions.py](actions.py)  
- LLM adapter and types: [`llm.agent`](llm.py), [`llm.File`](llm.py), [`llm.handle_attachments`](llm.py), [`llm.is_image`](llm.py) — [llm.py](llm.py)  
- Mock evaluators for local testing: [mock_evaluators/r1_evaluator.py](mock_evaluators/r1_evaluator.py), [mock_evaluators/r2_evaluator.py](mock_evaluators/r2_evaluator.py), [mock_evaluators/initial.py](mock_evaluators/initial.py)  
- Dockerfile: [Dockerfile](Dockerfile)  
- Python deps: [requirements.txt](requirements.txt)  
- Example local env: [local.example.env](local.example.env)

## Features
- Receives task payloads at POST /handle_task and executes asynchronously (background task). See [`app.handle_task`](app.py).
- Generates website code using a configured LLM agent and pushes files into a GitHub repository. See [`actions.write_code`](actions.py) and [`llm.agent`](llm.py).
- Enables GitHub Pages and reports back evaluation metadata to an evaluation endpoint with retries. See [`actions.enable_github_pages`](actions.py) and [`actions.send_evaluation_response`](actions.py).
- Local mock evaluation servers to accept evaluation callbacks for development. See [mock_evaluators](mock_evaluators/).

## Getting started (local)

1. Install dependencies (recommended inside a venv)
```sh
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

2. Create a local environment file from the example:
```sh
cp local.example.env local.env
# edit local.env to set GITHUB_TOKEN, secret, OPENAI_API_KEY, etc.
```
See [`local.example.env`](local.example.env).

3. Run the mock evaluators (optional, for local round testing)
```sh
# run evaluator for round 1
python mock_evaluators/r1_evaluator.py

# run evaluator for round 2
python mock_evaluators/r2_evaluator.py
```

4. Start the main app
```sh
python app.py
# or using uvicorn:
uvicorn app:app --host 0.0.0.0 --port 8080
```

5. Send a sample task (the repo includes a sample helper)
```sh
python mock_evaluators/initial.py
```
This posts a sample payload to the running app and prints the response. See [mock_evaluators/initial.py](mock_evaluators/initial.py).

## API

POST /handle_task
- Accepts a JSON payload describing the task. If the provided `secret` doesn't match the `secret` env var, returns `{"error":"Invalid credentials"}`.
- The endpoint schedules a background job that:
  - Generates/updates files via [`actions.write_code`](actions.py) using [`llm.agent`](llm.py).
  - Creates or updates a GitHub repo and enables Pages.
  - Posts an evaluation callback to the `evaluation_url` in the payload using [`actions.send_evaluation_response`](actions.py).

Minimal payload fields used by the service:
- email, secret, task, round, nonce, brief, checks, attachments, evaluation_url

Refer to the example in [mock_evaluators/initial.py](mock_evaluators/initial.py).

## How it works (high level)
1. Incoming POST to [`app.handle_task`](app.py) validates the secret and schedules a background job.
2. Background job calls into functions in [actions.py](actions.py):
   - Use the LLM via [`actions.write_code`](actions.py) (which delegates to [`llm.agent`](llm.py)) to produce files.
   - Push files to GitHub via [`actions.push_files`](actions.py).
   - Enable Pages via [`actions.enable_github_pages`](actions.py) and obtain URLs.
   - Report evaluation metadata back to the caller via [`actions.send_evaluation_response`](actions.py), with exponential backoff & retries.
3. Mock evaluators in [mock_evaluators/](mock_evaluators/) implement a simple /evaluate endpoint used by initial rounds in development.

## Development notes & troubleshooting

> [!warning]
> Ensure you set the `GITHUB_TOKEN` and `secret` environment variables before running anything that talks to GitHub. The code uses `GITHUB_TOKEN` via headers in [actions.py](actions.py).

- LLM configuration: the project uses a pydantic-ai Agent configured in [`llm.agent`](llm.py). If you change the LLM or model, update that file.
- If GitHub repo creation fails, the HTTP response text is raised by [`actions.create_github_repo`](actions.py) — inspect logs and token scopes.
- For local testing, run the evaluator servers first, then the app, and use [mock_evaluators/initial.py](mock_evaluators/initial.py) to post a task.

## Useful commands

- Run app locally:
```sh
uvicorn app:app --host 0.0.0.0 --port 8080
```

- Build & run Docker (image exposes the app):
```sh
docker build -t tds-deploy .
docker run --env-file local.env -p 8080:7860 tds-deploy
```
> [!note]
> Dockerfile's CMD uses port 7860; the app.py default run uses 8080. When running with Docker, map ports appropriately.

## Files of interest
- [app.py](app.py) — main FastAPI app and background task orchestration.
- [actions.py](actions.py) — GitHub and evaluation-side effects and LLM invocation.
- [llm.py](llm.py) — agent wiring, File model and attachment helpers.
- [mock_evaluators/](mock_evaluators/) — local fake evaluators and a task sender for testing.
- [Dockerfile](Dockerfile) — containerization.
- [requirements.txt](requirements.txt) — pinned Python dependencies.

## Contributing / next steps
> [!note]
> This README intentionally focuses on usage and developer orientation. See the repository for existing TODOs in code comments (notably around round-2 flow and deployment automation).