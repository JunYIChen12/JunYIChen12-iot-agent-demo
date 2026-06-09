import json
import os
import random
import time
from datetime import datetime, timezone

import paho.mqtt.client as mqtt


MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
PRODUCT_KEY = os.getenv("PRODUCT_KEY", "TEMP_SENSOR")
DEVICE_NAME = os.getenv("DEVICE_NAME", "demo-device-001")
DEVICE_SECRET = os.getenv("DEVICE_SECRET", "demo-secret")
TOPIC_PREFIX = os.getenv("DEMO_TOPIC_PREFIX", "/demo")


def main() -> None:
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"{PRODUCT_KEY}.{DEVICE_NAME}")
    client.username_pw_set(f"{DEVICE_NAME}&{PRODUCT_KEY}", DEVICE_SECRET)
    client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
    client.loop_start()

    topic = f"{TOPIC_PREFIX}/sys/{PRODUCT_KEY}/{DEVICE_NAME}/thing/event/property/post"
    print(f"simulator publishing to {topic}")

    while True:
        payload = {
            "id": str(int(time.time() * 1000)),
            "version": "1.0",
            "method": "thing.event.property.post",
            "sys": {"ack": 0},
            "params": {
                "temperature": round(random.uniform(20, 62), 2),
                "humidity": round(random.uniform(35, 85), 2),
                "battery": random.randint(30, 100),
            },
            "time": datetime.now(timezone.utc).isoformat(),
        }
        client.publish(topic, json.dumps(payload), qos=0)
        print(payload)
        time.sleep(5)


if __name__ == "__main__":
    main()
