# IoT Agent Demo

Open-source personal demo inspired by the BladeX IoT architecture:

`category thing model -> product inheritance/extension -> device -> MQTT/HTTP ingest -> effective thing model validation -> storage -> rules -> dashboard -> AI assistant`

Current working version: `v0.2.0-dev`.

## Services

- `backend`: FastAPI API, business data, OpenAPI, simple AI assistant.
- `data-worker`: MQTT subscriber, message parser, model validator, rule trigger.
- `frontend`: Vue 3 dashboard and management console.
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

## Demo Acceptance Chain

The current demo can show:

```text
create category -> create product -> configure thing model -> create device
-> simulator publishes MQTT telemetry -> backend shows device online
-> dashboard shows latest data and trend -> rule triggers alarm
-> AI explains why the device alarm fired
```

The thing model layer follows the hierarchy used by BladeX-style IoT platforms:

```text
category common thing model -> product inherits and extends -> device owns the final product model
```

Telemetry is accepted only when the product is published/online, the device
secret matches, and every reported property exists in the effective thing model.
