from datetime import datetime, timezone
from operator import eq, ge, gt, le, lt, ne
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models import AlarmLog, CategoryThingModel, Device, DevicePropertyLog, Product, Rule, ThingModel


OPS = {
    ">": gt,
    ">=": ge,
    "<": lt,
    "<=": le,
    "==": eq,
    "!=": ne,
}


def ingest_property_payload(
    db: Session,
    product_key: str,
    device_name: str,
    params: dict[str, Any],
    sys: dict[str, Any] | None = None,
) -> dict[str, Any]:
    product = db.scalar(select(Product).where(Product.product_key == product_key))
    if not product:
        return {"accepted": False, "errors": [f"Unknown productKey: {product_key}"]}
    if product.status not in {"online", "published"}:
        return {
            "accepted": False,
            "errors": [f"Product {product_key} is not published"],
        }

    device = db.scalar(
        select(Device).where(Device.product_id == product.id, Device.device_name == device_name)
    )
    if not device:
        return {"accepted": False, "errors": [f"Unknown deviceName: {device_name}"]}
    credential_errors = _validate_device_credentials(product_key, device, sys or {})
    if credential_errors:
        return {"accepted": False, "errors": credential_errors}

    model_rows = effective_thing_models(db, product, "property")
    model_map = {m.identifier: m for m in model_rows}
    errors: list[str] = []
    accepted: dict[str, Any] = {}

    for key, raw_value in params.items():
        if key not in model_map:
            errors.append(f"Property {key} is not defined in thing model")
            continue
        value = raw_value.get("value") if isinstance(raw_value, dict) and "value" in raw_value else raw_value
        if not _validate_type(value, model_map[key].data_type):
            errors.append(f"Property {key} expects {model_map[key].data_type}, got {type(value).__name__}")
            continue
        accepted[key] = value
        db.add(
            DevicePropertyLog(
                product_key=product_key,
                device_name=device_name,
                identifier=key,
                value=str(value),
            )
        )

    now = datetime.now(timezone.utc)
    if accepted:
        device.status = "online"
        device.last_online_at = device.last_online_at or now
        device.last_report_at = now
        device.latest_properties = {**(device.latest_properties or {}), **accepted}
        _evaluate_rules(db, product, device, accepted)

    db.commit()
    return {"accepted": bool(accepted), "properties": accepted, "errors": errors}


def _validate_device_credentials(product_key: str, device: Device, sys: dict[str, Any]) -> list[str]:
    expected_username = f"{device.device_name}&{product_key}"
    username = sys.get("username")
    device_secret = sys.get("deviceSecret") or sys.get("device_secret") or sys.get("password")
    errors: list[str] = []
    if username and username != expected_username:
        errors.append("Invalid device username")
    if device_secret != device.device_secret:
        errors.append("Invalid device secret")
    return errors


def latest_logs(db: Session, limit: int = 30) -> list[DevicePropertyLog]:
    return db.scalars(
        select(DevicePropertyLog).order_by(desc(DevicePropertyLog.reported_at)).limit(limit)
    ).all()


def effective_thing_models(
    db: Session,
    product: Product,
    model_type: str | None = None,
) -> list[CategoryThingModel | ThingModel]:
    category_stmt = select(CategoryThingModel).where(CategoryThingModel.category_id == product.category_id)
    product_stmt = select(ThingModel).where(ThingModel.product_id == product.id)
    if model_type:
        category_stmt = category_stmt.where(CategoryThingModel.model_type == model_type)
        product_stmt = product_stmt.where(ThingModel.model_type == model_type)

    inherited = db.scalars(category_stmt.order_by(CategoryThingModel.id)).all()
    product_specific = db.scalars(product_stmt.order_by(ThingModel.id)).all()

    merged: dict[tuple[str, str], CategoryThingModel | ThingModel] = {}
    for row in inherited:
        merged[(row.identifier, row.model_type)] = row
    for row in product_specific:
        merged[(row.identifier, row.model_type)] = row
    return list(merged.values())


def _validate_type(value: Any, data_type: str) -> bool:
    if data_type in {"float", "double"}:
        return _can_float(value)
    if data_type in {"int", "integer"}:
        return _can_int(value)
    if data_type in {"bool", "boolean"}:
        return isinstance(value, bool) or str(value).lower() in {"true", "false", "0", "1"}
    return isinstance(value, (str, int, float, bool))


def _can_float(value: Any) -> bool:
    try:
        float(value)
        return True
    except (TypeError, ValueError):
        return False


def _can_int(value: Any) -> bool:
    try:
        return float(value).is_integer()
    except (TypeError, ValueError):
        return False


def _evaluate_rules(db: Session, product: Product, device: Device, values: dict[str, Any]) -> None:
    rules = db.scalars(
        select(Rule).where(Rule.product_id == product.id, Rule.enabled.is_(True))
    ).all()
    for rule in rules:
        if rule.identifier not in values:
            continue
        op = OPS.get(rule.operator)
        if not op:
            continue
        try:
            triggered = op(float(values[rule.identifier]), float(rule.threshold))
        except (TypeError, ValueError):
            triggered = op(str(values[rule.identifier]), str(rule.threshold))
        if triggered:
            message = rule.message.rstrip("。.,， ")
            db.add(
                AlarmLog(
                    rule_id=rule.id,
                    product_key=product.product_key,
                    device_name=device.device_name,
                    content=f"{message}，当前值 {values[rule.identifier]}",
                )
            )
