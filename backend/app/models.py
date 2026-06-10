from datetime import datetime
from enum import Enum

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class DeviceStatus(str, Enum):
    offline = "offline"
    online = "online"


class ModelType(str, Enum):
    property = "property"
    command = "command"
    event = "event"


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    industry: Mapped[str] = mapped_column(String(120), default="demo")
    scene: Mapped[str] = mapped_column(String(120), default="demo")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    products: Mapped[list["Product"]] = relationship(back_populates="category")
    thing_models: Mapped[list["CategoryThingModel"]] = relationship(back_populates="category")


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"))
    product_key: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(160))
    protocol: Mapped[str] = mapped_column(String(40), default="mqtt")
    status: Mapped[str] = mapped_column(String(40), default="development")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    category: Mapped[Category] = relationship(back_populates="products")
    devices: Mapped[list["Device"]] = relationship(back_populates="product")
    thing_models: Mapped[list["ThingModel"]] = relationship(back_populates="product")


class Device(Base):
    __tablename__ = "devices"
    __table_args__ = (UniqueConstraint("product_id", "device_name", name="uq_device_product_name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    device_name: Mapped[str] = mapped_column(String(120), index=True)
    device_secret: Mapped[str] = mapped_column(String(120))
    unique_no: Mapped[str] = mapped_column(String(160), unique=True)
    status: Mapped[str] = mapped_column(String(40), default=DeviceStatus.offline.value)
    last_online_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_report_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    latest_properties: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    product: Mapped[Product] = relationship(back_populates="devices")


class ThingModel(Base):
    __tablename__ = "thing_models"
    __table_args__ = (UniqueConstraint("product_id", "identifier", "model_type", name="uq_model_identifier_type"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    identifier: Mapped[str] = mapped_column(String(120))
    name: Mapped[str] = mapped_column(String(160))
    model_type: Mapped[str] = mapped_column(String(40), default=ModelType.property.value)
    data_type: Mapped[str] = mapped_column(String(40), default="float")
    unit: Mapped[str] = mapped_column(String(40), default="")
    access_mode: Mapped[str] = mapped_column(String(40), default="read")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    product: Mapped[Product] = relationship(back_populates="thing_models")


class CategoryThingModel(Base):
    __tablename__ = "category_thing_models"
    __table_args__ = (
        UniqueConstraint("category_id", "identifier", "model_type", name="uq_category_model_identifier_type"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"))
    identifier: Mapped[str] = mapped_column(String(120))
    name: Mapped[str] = mapped_column(String(160))
    model_type: Mapped[str] = mapped_column(String(40), default=ModelType.property.value)
    data_type: Mapped[str] = mapped_column(String(40), default="float")
    unit: Mapped[str] = mapped_column(String(40), default="")
    access_mode: Mapped[str] = mapped_column(String(40), default="read")
    required: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    category: Mapped[Category] = relationship(back_populates="thing_models")


class DevicePropertyLog(Base):
    __tablename__ = "device_property_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_key: Mapped[str] = mapped_column(String(80), index=True)
    device_name: Mapped[str] = mapped_column(String(120), index=True)
    identifier: Mapped[str] = mapped_column(String(120), index=True)
    value: Mapped[str] = mapped_column(Text)
    reported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


class DeviceMessageLog(Base):
    __tablename__ = "device_message_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_key: Mapped[str] = mapped_column(String(80), index=True)
    device_name: Mapped[str] = mapped_column(String(120), index=True)
    topic: Mapped[str] = mapped_column(String(300), index=True)
    direction: Mapped[str] = mapped_column(String(40), default="up")
    payload: Mapped[dict] = mapped_column(JSONB, default=dict)
    reported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


class Rule(Base):
    __tablename__ = "rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(160))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    identifier: Mapped[str] = mapped_column(String(120))
    operator: Mapped[str] = mapped_column(String(20), default=">")
    threshold: Mapped[float] = mapped_column()
    message: Mapped[str] = mapped_column(String(240))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AlarmLog(Base):
    __tablename__ = "alarm_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    rule_id: Mapped[int] = mapped_column(ForeignKey("rules.id"))
    product_key: Mapped[str] = mapped_column(String(80))
    device_name: Mapped[str] = mapped_column(String(120))
    content: Mapped[str] = mapped_column(Text)
    triggered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
