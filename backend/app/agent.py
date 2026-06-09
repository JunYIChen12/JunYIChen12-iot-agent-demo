from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models import AlarmLog, Device, DevicePropertyLog, Product, ThingModel


def answer_agent_message(db: Session, message: str) -> dict:
    msg = message.strip().lower()
    actions: list[str] = []

    if any(word in msg for word in ["离线", "offline", "为什么"]):
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
        reason = "设备当前在线。" if device.status == "online" else "设备当前离线，可能是模拟器未启动、MQTT连接失败或设备密钥不一致。"
        detail = f"最后上报时间: {device.last_report_at}" if latest else "还没有收到该设备的属性上报。"
        return {"answer": f"{device.device_name}: {reason} {detail}", "actions": ["query_device_status", "query_device_logs"]}

    if any(word in msg for word in ["报文", "payload", "topic", "校验"]):
        return {
            "answer": "报文校验规则：Topic 使用 /demo/sys/{productKey}/{deviceName}/thing/event/property/post，payload 的 params 字段必须匹配产品物模型。例如 temperature、humidity、battery。",
            "actions": ["explain_topic_schema", "validate_payload"],
        }

    if any(word in msg for word in ["模型", "物模型", "属性"]):
        product = db.scalar(select(Product).where(Product.product_key == "TEMP_SENSOR"))
        if not product:
            return {"answer": "当前没有演示产品。", "actions": ["query_product"]}
        models = db.scalars(select(ThingModel).where(ThingModel.product_id == product.id)).all()
        text = "、".join([f"{m.identifier}({m.data_type}{m.unit})" for m in models])
        return {"answer": f"TEMP_SENSOR 的物模型属性包括：{text}。", "actions": ["query_thing_model"]}

    if any(word in msg for word in ["告警", "报警", "异常"]):
        alarms = db.scalars(select(AlarmLog).order_by(desc(AlarmLog.triggered_at)).limit(3)).all()
        if not alarms:
            return {"answer": "当前还没有告警。你可以等模拟器上报温度超过 50 后再看。", "actions": ["query_alarm"]}
        lines = [f"{a.device_name}: {a.content} ({a.triggered_at})" for a in alarms]
        return {"answer": "最近告警：\n" + "\n".join(lines), "actions": ["query_alarm"]}

    return {
        "answer": "我可以帮你查设备离线原因、解释 MQTT Topic、查看物模型、总结最近告警。第一版暂不直接自动改配置。",
        "actions": ["help"],
    }


def _find_device(db: Session, message: str) -> Device | None:
    devices = db.scalars(select(Device)).all()
    for device in devices:
        if device.device_name in message:
            return device
    return devices[0] if devices else None
