# IoT Agent Demo

Open-source personal demo inspired by the BladeX IoT architecture:

`category -> product -> device -> MQTT/HTTP ingest -> thing model validation -> storage -> rules -> dashboard -> AI assistant`

## Services

- `backend`: FastAPI API, business data, OpenAPI, simple AI assistant.
- `data-worker`: MQTT subscriber, message parser, model validator, rule trigger.
- `frontend`: Vue 3 dashboard.
- `simulator`: Python MQTT device simulator.
- `emqx`: MQTT broker.
- `postgres`: business data and first-version time-series logs.
- `redis`: online status/cache.

## Run

1. Start Docker Desktop and enable WSL integration.
2. From this folder:

```powershell
docker compose up --build
```

3. Open:

- Frontend: http://localhost:5173
- Backend API docs: http://localhost:8000/docs
- EMQX dashboard: http://localhost:18083, user `admin`, password `public`

The backend seeds one product and one device matching the simulator.
