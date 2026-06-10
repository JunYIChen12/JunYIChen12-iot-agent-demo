import json
import signal
import time

import paho.mqtt.client as mqtt
from sqlalchemy.orm import Session

from app.config import settings
from app.db import Base, engine
from app.seed import seed_demo_data
from app.services import ingest_property_payload


running = True


def main() -> None:
    Base.metadata.create_all(bind=engine)
    with Session(engine) as db:
        seed_demo_data(db)

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="iot-demo-data-worker")
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(settings.mqtt_host, settings.mqtt_port, keepalive=60)
    client.loop_start()

    signal.signal(signal.SIGTERM, _stop)
    signal.signal(signal.SIGINT, _stop)
    print("data-worker started")
    while running:
        time.sleep(1)

    client.loop_stop()
    client.disconnect()


def on_connect(client: mqtt.Client, userdata, flags, reason_code, properties) -> None:
    topic = f"{settings.demo_topic_prefix}/sys/+/+/thing/event/property/post"
    client.subscribe(topic)
    print(f"subscribed {topic}")


def on_message(client: mqtt.Client, userdata, msg: mqtt.MQTTMessage) -> None:
    parts = msg.topic.strip("/").split("/")
    if len(parts) < 7:
        print(f"ignored invalid topic: {msg.topic}")
        return
    product_key = parts[2]
    device_name = parts[3]
    try:
        payload = json.loads(msg.payload.decode("utf-8"))
    except json.JSONDecodeError as exc:
        print(f"invalid json topic={msg.topic} error={exc}")
        return

    params = payload.get("params", payload)
    sys = payload.get("sys", {})
    if not isinstance(params, dict):
        print(f"invalid params topic={msg.topic}")
        return
    if not isinstance(sys, dict):
        print(f"invalid sys topic={msg.topic}")
        return

    with Session(engine) as db:
        result = ingest_property_payload(db, product_key, device_name, params, sys, msg.topic, payload)
        print(f"ingest topic={msg.topic} result={result}")


def _stop(signum, frame) -> None:
    global running
    running = False


if __name__ == "__main__":
    main()
