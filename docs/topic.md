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
  "sys": {
    "ack": 0,
    "username": "demo-device-001&TEMP_SENSOR",
    "deviceSecret": "demo-secret"
  },
  "params": {
    "temperature": 25.5,
    "humidity": 60.2,
    "battery": 88
  }
}
```

The backend accepts the report only when:

- the product exists and is published/online;
- the device exists under that product;
- `sys.username` is `{deviceName}&{productKey}` when provided;
- `sys.deviceSecret` matches the registered device secret;
- every `params` field exists in the effective thing model.

## HTTP Property Report

```text
POST /openapi/thing/{productKey}/{deviceName}/property/post
```
