from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models import AlarmLog, Device, DevicePropertyLog, Product, ThingModel


def answer_agent_message(db: Session, message: str) -> dict:
    raw_message = message.strip()
    msg = raw_message.lower()

    if _asks_about_alarm(msg):
        return _answer_alarm_question(db, raw_message)

    if _asks_about_status(msg):
        return _answer_status_question(db, raw_message)

    if any(word in msg for word in ["报文", "payload", "topic", "校验"]):
        return {
            "answer": (
                "演示链路使用 /demo/sys/{productKey}/{deviceName}/thing/event/property/post。"
                "payload 的 params 字段必须匹配产品物模型，例如 temperature、humidity、battery。"
            ),
            "actions": ["explain_topic_schema", "validate_payload"],
        }

    if any(word in msg for word in ["模型", "物模型", "属性", "thing model"]):
        product = db.scalar(select(Product).where(Product.product_key == "TEMP_SENSOR"))
        if not product:
            return {"answer": "当前还没有演示产品。", "actions": ["query_product"]}
        models = db.scalars(select(ThingModel).where(ThingModel.product_id == product.id)).all()
        text = "、".join([f"{m.identifier}({m.data_type}{m.unit})" for m in models])
        return {"answer": f"TEMP_SENSOR 的物模型属性包括：{text}。", "actions": ["query_thing_model"]}

    return {
        "answer": (
            "我可以帮你查设备在线状态、解释 MQTT Topic、查看物模型、总结最近告警，"
            "也可以回答“为什么 demo-device-001 告警”。第一版暂不自动修改配置。"
        ),
        "actions": ["help"],
    }


def _asks_about_alarm(msg: str) -> bool:
    return any(word in msg for word in ["告警", "报警", "异常", "alarm"])


def _asks_about_status(msg: str) -> bool:
    return any(word in msg for word in ["离线", "在线", "offline", "online", "状态"])


def _answer_alarm_question(db: Session, message: str) -> dict:
    device = _find_device(db, message)
    stmt = select(AlarmLog).order_by(desc(AlarmLog.triggered_at)).limit(3)
    if device:
        stmt = (
            select(AlarmLog)
            .where(AlarmLog.device_name == device.device_name)
            .order_by(desc(AlarmLog.triggered_at))
            .limit(3)
        )
    alarms = db.scalars(stmt).all()

    if not alarms:
        target = f"{device.device_name} " if device else ""
        return {
            "answer": (
                f"当前没有查到 {target}告警。你可以确认模拟器是否正在上报，"
                "或者等 temperature 超过 50 后再观察规则触发。"
            ),
            "actions": ["query_alarm", "query_rule"],
        }

    lines = []
    for alarm in alarms:
        latest_value = _latest_value(db, alarm.device_name, "temperature")
        value_text = f"最近 temperature={latest_value.value}" if latest_value else "没有查到最近温度值"
        lines.append(
            f"{alarm.device_name}: {alarm.content}。原因是规则检测到温度超过阈值 50，{value_text}，触发时间 {alarm.triggered_at}。"
        )

    return {
        "answer": "最近告警解释：\n" + "\n".join(lines),
        "actions": ["query_alarm", "query_rule", "query_device_logs"],
    }


def _answer_status_question(db: Session, message: str) -> dict:
    device = _find_device(db, message)
    if not device:
        return {
            "answer": "我没有找到你提到的设备。你可以输入设备名，例如 demo-device-001。",
            "actions": ["query_device_status"],
        }

    latest = db.scalar(
        select(DevicePropertyLog)
        .where(DevicePropertyLog.device_name == device.device_name)
        .order_by(desc(DevicePropertyLog.reported_at))
    )
    if device.status == "online":
        reason = "设备当前在线，说明 MQTT 或 HTTP 上报链路已经打通。"
    else:
        reason = "设备当前离线，常见原因是模拟器未启动、MQTT 连接失败或设备密钥不一致。"
    detail = f"最后上报时间 {latest.reported_at}" if latest else "还没有收到该设备的属性上报。"
    return {
        "answer": f"{device.device_name}: {reason} {detail}",
        "actions": ["query_device_status", "query_device_logs"],
    }


def _find_device(db: Session, message: str) -> Device | None:
    devices = db.scalars(select(Device)).all()
    for device in devices:
        if device.device_name in message:
            return device
    return devices[0] if devices else None


def _latest_value(db: Session, device_name: str, identifier: str) -> DevicePropertyLog | None:
    return db.scalar(
        select(DevicePropertyLog)
        .where(DevicePropertyLog.device_name == device_name, DevicePropertyLog.identifier == identifier)
        .order_by(desc(DevicePropertyLog.reported_at))
    )
