from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class CategoryCreate(BaseModel):
    name: str
    industry: str = "demo"
    scene: str = "demo"


class ProductCreate(BaseModel):
    category_id: int
    product_key: str
    name: str
    protocol: str = "mqtt"


class DeviceCreate(BaseModel):
    product_id: int
    device_name: str
    device_secret: str
    unique_no: str


class ThingModelCreate(BaseModel):
    product_id: int
    identifier: str
    name: str
    model_type: str = "property"
    data_type: str = "float"
    unit: str = ""
    access_mode: str = "read"


class CategoryThingModelCreate(BaseModel):
    category_id: int
    identifier: str
    name: str
    model_type: str = "property"
    data_type: str = "float"
    unit: str = ""
    access_mode: str = "read"
    required: bool = True


class RuleCreate(BaseModel):
    name: str
    product_id: int
    identifier: str
    operator: str = ">"
    threshold: float
    message: str
    enabled: bool = True


class HttpPropertyPost(BaseModel):
    id: str | None = None
    version: str = "1.0"
    sys: dict[str, Any] = Field(default_factory=dict)
    params: dict[str, Any] = Field(default_factory=dict)


class AgentRequest(BaseModel):
    message: str


class AgentResponse(BaseModel):
    answer: str
    actions: list[str] = Field(default_factory=list)


class DashboardStats(BaseModel):
    categories: int
    products: int
    devices: int
    online_devices: int
    property_logs: int
    alarms: int


class TrendPoint(BaseModel):
    reported_at: datetime
    identifier: str
    value: str
