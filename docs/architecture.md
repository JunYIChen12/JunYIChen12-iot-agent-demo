# Architecture

This project follows the same broad shape as a BladeX-style IoT platform, but uses free and open-source components.

## Target Chain

```text
category -> product -> device -> MQTT/HTTP ingest -> topic routing -> thing model validation -> storage -> rule alarm -> dashboard -> AI assistant
```

## Component Mapping

| Platform Role | Responsibility | Demo Implementation |
| --- | --- | --- |
| `blade-server` style business service | OpenAPI, device/product/rule management, dashboard APIs | `backend` with FastAPI |
| `blade-broker` style message broker | MQTT connectivity and topic routing | EMQX Community |
| `blade-data` style data flow service | Subscribe, parse, validate, store, trigger rules | `data-worker` |
| Business database | Products, devices, models, rules, alarms | PostgreSQL |
| Cache/status layer | Online state and future cache/pub-sub | Redis |
| Device simulator | Generates telemetry for demos | Python `paho-mqtt` simulator |
| Frontend console | Dashboard and operator UI | Vue 3, Element Plus, ECharts |
| AI assistant | Human-friendly diagnosis and platform guidance | FastAPI endpoint with rule-based tools |

## Runtime Flow

```mermaid
flowchart TD
    A["Simulator / Device"] --> B["EMQX MQTT Broker"]
    B --> C["data-worker"]
    C --> D["Topic Parser"]
    D --> E["Thing Model Validator"]
    E --> F["PostgreSQL Property Logs"]
    E --> G["Device Status Update"]
    E --> H["Threshold Rule Engine"]
    H --> I["Alarm Logs"]
    F --> J["FastAPI Dashboard API"]
    G --> J
    I --> J
    J --> K["Vue Management Console"]
    J --> L["AI Assistant"]
```

## Management Flow

```mermaid
flowchart LR
    A["Create Category"] --> B["Create Product"]
    B --> C["Configure Thing Model"]
    C --> D["Create Device"]
    D --> E["Start Simulator"]
    E --> F["MQTT Property Report"]
    F --> G["Device Online"]
    F --> H["Latest Data and Trend"]
    F --> I["Threshold Rule Alarm"]
    I --> J["AI Alarm Explanation"]
```

## Topic Protocol

The demo uses `/demo` as the prefix instead of copying a vendor namespace.

```text
/demo/sys/{productKey}/{deviceName}/thing/event/property/post
```

Example product and device:

```text
productKey: TEMP_SENSOR
deviceName: demo-device-001
deviceSecret: demo-secret
```

Payload:

```json
{
  "id": "1700000000000",
  "version": "1.0",
  "method": "thing.event.property.post",
  "params": {
    "temperature": 25.5,
    "humidity": 60.2,
    "battery": 88
  }
}
```

## Current Scope

Included:

- Single-node Docker Compose environment.
- One seeded category, product, device, thing model, and threshold rule.
- MQTT property reports.
- First-version property log storage in PostgreSQL.
- Dashboard and rule alarm display.
- Management console for categories, products, devices, thing models, and rules.
- Rule-based AI assistant with alarm explanation.

Deferred:

- MQTT broker-level credential enforcement.
- Device shadow.
- OTA.
- Kafka/Redpanda message bus.
- TDengine/InfluxDB/TimescaleDB dedicated time-series backend.
- Multi-tenant RBAC.
- Node-RED edge workflow integration.
- Real LLM-backed agent tool calling.
