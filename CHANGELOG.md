# Changelog

All notable changes to this project are documented here.

## v0.2.0-dev - 2026-06-09

Management console iteration aligned with the BladeX-style commercial architecture.

### Added

- Sidebar management console with modules for overview, categories, products, devices, thing models, rules, logs, and AI assistant.
- Frontend create flows for categories, products, devices, thing model rows, and threshold rules.
- Category-level thing model definitions that products inherit.
- Product-level thing model extensions and effective product thing model API.
- Full data refresh across dashboard and management modules.
- AI assistant default prompt for explaining why `demo-device-001` triggered an alarm.
- BladeX-style chain mapping in the AI assistant page.

### Changed

- Backend version is now `0.2.0-dev`.
- Device telemetry validation now uses the effective thing model: category inherited definitions merged with product extensions.
- Seed data now puts `temperature` and `humidity` on the category and `battery` on the product.
- Seed data now normalizes the demo category, product, thing model, and rule on startup.
- Alarm explanation intent now takes priority over generic status diagnosis.
- Alarm content formatting avoids duplicated punctuation.

### Verified

- Docker images build for backend, data-worker, and frontend.
- Python backend modules compile.
- Frontend production build succeeds.
- HTTP property post triggers device online status, property logs, and temperature alarm.
- Browser verification confirms every management module opens and Chinese AI alarm explanation works.
- Browser verification confirms the thing model page shows category inheritance, product extension, and the final merged model.

### Still Deferred

- Dedicated manual property-post test page.
- Broker-level device credential enforcement.
- Formal `v0.2.0` release tag.

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
