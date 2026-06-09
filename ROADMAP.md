# Roadmap

This roadmap keeps the project moving as a traceable demo platform rather than a one-off prototype.

## v0.1.0 - Runnable Baseline

Status: complete

- Docker Compose stack.
- EMQX, PostgreSQL, Redis.
- FastAPI backend.
- MQTT data worker.
- Python simulator.
- Vue dashboard.
- Simple threshold rule alarms.
- Rule-based AI assistant.

## v0.2.0 - Management Console

Goal: make the platform configurable from the UI.

- Product CRUD page.
- Device CRUD page.
- Thing model editor.
- Rule editor.
- Manual property report testing.
- Broker credential alignment for demo devices.

## v0.3.0 - Device Control

Goal: support platform-to-device interaction.

- Command downlink topic.
- Command reply topic.
- Device command log.
- Basic device shadow: reported, desired, delta.
- Device simulator listens for commands.

## v0.4.0 - AI Agent Tool Calling

Goal: move from rule-based assistant to real agent workflow.

- LLM provider configuration.
- Safe tool registry.
- Natural-language product and thing model creation.
- MQTT payload validation tool.
- Device diagnosis tool.
- Rule generation tool.

## v0.5.0 - Time-Series and Observability

Goal: separate telemetry storage and improve operational visibility.

- Add TimescaleDB, InfluxDB, or TDengine.
- Migrate property logs to a dedicated time-series backend.
- Grafana dashboard option.
- Backend metrics endpoint.
- Structured logs.

## v0.6.0 - Edge and Workflow

Goal: add edge-style flow orchestration.

- Node-RED integration.
- Webhook action type.
- Flow-based rule examples.
- HTTP device integration examples.

## v1.0.0 - Stable Demo Platform

Goal: a clean, documented, repeatable personal IoT platform demo.

- Stable API contract.
- Stable topic protocol.
- Migration notes.
- Full setup guide.
- End-to-end tests for the core chain.
- Release screenshots and demo script.
