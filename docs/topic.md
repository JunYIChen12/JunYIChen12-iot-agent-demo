# Topic Protocol

This demo uses `/demo` as the protocol prefix.

## Property Report

```text
/demo/sys/{productKey}/{deviceName}/thing/event/property/post
```

Payload:

```json
{
  "id": "1700000000000",
  "version": "1.0",
  "method": "thing.event.property.post",
  "sys": { "ack": 0 },
  "params": {
    "temperature": 25.5,
    "humidity": 60.2,
    "battery": 88
  }
}
```

## HTTP Property Report

```text
POST /openapi/thing/{productKey}/{deviceName}/property/post
```
