from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Category, CategoryThingModel, Device, Product, Rule, ThingModel


def seed_demo_data(db: Session) -> None:
    category = db.scalar(select(Category).where(Category.name == "传感器"))
    if not category:
        category = Category(name="传感器", industry="智能工业", scene="环境监测")
        db.add(category)
        db.flush()
    else:
        category.industry = "智能工业"
        category.scene = "环境监测"

    product = db.scalar(select(Product).where(Product.product_key == "TEMP_SENSOR"))
    if not product:
        product = Product(
            category_id=category.id,
            product_key="TEMP_SENSOR",
            name="温湿度传感器",
            protocol="mqtt",
            status="online",
        )
        db.add(product)
        db.flush()
    else:
        product.category_id = category.id
        product.name = "温湿度传感器"
        product.protocol = "mqtt"
        product.status = "online"

    category_models = [
        ("temperature", "温度", "float", "C"),
        ("humidity", "湿度", "float", "%"),
    ]
    for identifier, name, data_type, unit in category_models:
        exists = db.scalar(
            select(CategoryThingModel).where(
                CategoryThingModel.category_id == category.id,
                CategoryThingModel.identifier == identifier,
                CategoryThingModel.model_type == "property",
            )
        )
        if not exists:
            db.add(
                CategoryThingModel(
                    category_id=category.id,
                    identifier=identifier,
                    name=name,
                    model_type="property",
                    data_type=data_type,
                    access_mode="read",
                    unit=unit,
                    required=True,
                )
            )
        else:
            exists.name = name
            exists.data_type = data_type
            exists.unit = unit
            exists.access_mode = "read"
            exists.required = True

    product_models = [
        ("temperature", "温度", "float", "C"),
        ("humidity", "湿度", "float", "%"),
        ("battery", "电量", "int", "%"),
    ]
    for identifier, name, data_type, unit in product_models:
        exists = db.scalar(
            select(ThingModel).where(
                ThingModel.product_id == product.id,
                ThingModel.identifier == identifier,
                ThingModel.model_type == "property",
            )
        )
        if identifier in {"temperature", "humidity"}:
            if exists:
                db.delete(exists)
            continue
        if not exists:
            db.add(
                ThingModel(
                    product_id=product.id,
                    identifier=identifier,
                    name=name,
                    model_type="property",
                    data_type=data_type,
                    access_mode="read",
                    unit=unit,
                )
            )
        else:
            exists.name = name
            exists.data_type = data_type
            exists.unit = unit
            exists.access_mode = "read"

    device = db.scalar(
        select(Device).where(Device.product_id == product.id, Device.device_name == "demo-device-001")
    )
    if not device:
        db.add(
            Device(
                product_id=product.id,
                device_name="demo-device-001",
                device_secret="demo-secret",
                unique_no="SN-DEMO-001",
            )
        )

    rule = db.scalar(select(Rule).where(Rule.name == "温度过高告警"))
    if not rule:
        db.add(
            Rule(
                product_id=product.id,
                name="温度过高告警",
                identifier="temperature",
                operator=">",
                threshold=50,
                message="温度超过 50C，请检查设备环境",
            )
        )
    else:
        rule.product_id = product.id
        rule.identifier = "temperature"
        rule.operator = ">"
        rule.threshold = 50
        rule.message = "温度超过 50C，请检查设备环境"
        rule.enabled = True

    db.commit()
