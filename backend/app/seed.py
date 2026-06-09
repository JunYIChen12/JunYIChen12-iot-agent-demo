from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Category, Device, Product, Rule, ThingModel


def seed_demo_data(db: Session) -> None:
    category = db.scalar(select(Category).where(Category.name == "传感器"))
    if not category:
        category = Category(name="传感器", industry="智能工业", scene="环境监测")
        db.add(category)
        db.flush()

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

    models = [
        ("temperature", "温度", "float", "C"),
        ("humidity", "湿度", "float", "%"),
        ("battery", "电量", "int", "%"),
    ]
    for identifier, name, data_type, unit in models:
        exists = db.scalar(
            select(ThingModel).where(
                ThingModel.product_id == product.id,
                ThingModel.identifier == identifier,
                ThingModel.model_type == "property",
            )
        )
        if not exists:
            db.add(
                ThingModel(
                    product_id=product.id,
                    identifier=identifier,
                    name=name,
                    model_type="property",
                    data_type=data_type,
                    unit=unit,
                    access_mode="read",
                )
            )

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
                message="温度超过 50C，请检查设备环境。",
            )
        )

    db.commit()
