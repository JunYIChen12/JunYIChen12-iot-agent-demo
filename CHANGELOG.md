# Changelog

All notable changes to this project are documented here.

## v0.1.0 - 2026-06-09

First runnable personal IoT Agent Demo baseline.

### Added

- Docker Compose environment with EMQX, PostgreSQL, Redis, backend, data worker, simulator, and frontend.
- FastAPI backend with startup schema creation and seeded demo data.
- Business models for categories, products, devices, thing models, property logs, rules, and alarms.
- MQTT data worker subscribing to `/demo/sys/+/+/thing/event/property/post`.
- Python MQTT simulator for `TEMP_SENSOR/demo-device-001`.
- Vue 3 dashboard with metrics, device status, property logs, temperature trend, alarms, and AI assistant panel.
- Lightweight AI assistant endpoint for topic explanation, thing model lookup, device diagnosis, and alarm summary.
- Topic protocol documentation.
- Versioning strategy for long-term traceability.

### Verified

- Backend health endpoint returns OK.
- MQTT simulator publishes telemetry through EMQX.
- Data worker validates and stores property reports.
- Device online state updates from telemetry.
- Temperature rule triggers alarms when value exceeds `50`.
- Frontend renders live dashboard data from the backend.

### Known Limits

- PostgreSQL currently stores both business data and first-version time-series logs.
- Rule engine supports simple threshold rules only.
- AI assistant is rule-based in v0.1.0 and does not yet call an LLM provider.
- Device authentication is modeled in data but not enforced at the MQTT broker level yet.
