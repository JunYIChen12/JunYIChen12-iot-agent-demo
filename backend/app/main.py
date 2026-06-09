from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.agent import answer_agent_message
from app.db import Base, engine, get_db
from app.models import AlarmLog, Category, Device, DevicePropertyLog, Product, Rule, ThingModel
from app.schemas import (
    AgentRequest,
    CategoryCreate,
    DeviceCreate,
    HttpPropertyPost,
    ProductCreate,
    RuleCreate,
    ThingModelCreate,
)
from app.seed import seed_demo_data
from app.services import ingest_property_payload


app = FastAPI(title="IoT Agent Demo", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)
    with Session(engine) as db:
        seed_demo_data(db)


@app.get("/health")
def health() -> dict:
    return {"ok": True}


@app.get("/api/dashboard")
def dashboard(db: Session = Depends(get_db)) -> dict:
    return {
        "stats": {
            "categories": db.scalar(select(func.count(Category.id))),
            "products": db.scalar(select(func.count(Product.id))),
            "devices": db.scalar(select(func.count(Device.id))),
            "online_devices": db.scalar(select(func.count(Device.id)).where(Device.status == "online")),
            "property_logs": db.scalar(select(func.count(DevicePropertyLog.id))),
            "alarms": db.scalar(select(func.count(AlarmLog.id))),
        },
        "devices": [_device_dict(d) for d in db.scalars(select(Device).order_by(Device.id)).all()],
        "latest_logs": [_log_dict(l) for l in db.scalars(select(DevicePropertyLog).order_by(desc(DevicePropertyLog.reported_at)).limit(20)).all()],
        "alarms": [_alarm_dict(a) for a in db.scalars(select(AlarmLog).order_by(desc(AlarmLog.triggered_at)).limit(20)).all()],
    }


@app.get("/api/categories")
def list_categories(db: Session = Depends(get_db)) -> list[dict]:
    return [_category_dict(c) for c in db.scalars(select(Category).order_by(Category.id)).all()]


@app.post("/api/categories")
def create_category(payload: CategoryCreate, db: Session = Depends(get_db)) -> dict:
    row = Category(**payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return _category_dict(row)


@app.get("/api/products")
def list_products(db: Session = Depends(get_db)) -> list[dict]:
    return [_product_dict(p) for p in db.scalars(select(Product).order_by(Product.id)).all()]


@app.post("/api/products")
def create_product(payload: ProductCreate, db: Session = Depends(get_db)) -> dict:
    row = Product(**payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return _product_dict(row)


@app.get("/api/devices")
def list_devices(db: Session = Depends(get_db)) -> list[dict]:
    return [_device_dict(d) for d in db.scalars(select(Device).order_by(Device.id)).all()]


@app.post("/api/devices")
def create_device(payload: DeviceCreate, db: Session = Depends(get_db)) -> dict:
    row = Device(**payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return _device_dict(row)


@app.get("/api/thing-models")
def list_thing_models(product_id: int | None = None, db: Session = Depends(get_db)) -> list[dict]:
    stmt = select(ThingModel).order_by(ThingModel.id)
    if product_id:
        stmt = stmt.where(ThingModel.product_id == product_id)
    return [_thing_model_dict(m) for m in db.scalars(stmt).all()]


@app.post("/api/thing-models")
def create_thing_model(payload: ThingModelCreate, db: Session = Depends(get_db)) -> dict:
    row = ThingModel(**payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return _thing_model_dict(row)


@app.get("/api/rules")
def list_rules(db: Session = Depends(get_db)) -> list[dict]:
    return [_rule_dict(r) for r in db.scalars(select(Rule).order_by(Rule.id)).all()]


@app.post("/api/rules")
def create_rule(payload: RuleCreate, db: Session = Depends(get_db)) -> dict:
    row = Rule(**payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return _rule_dict(row)


@app.post("/openapi/thing/{product_key}/{device_name}/property/post")
def http_property_post(
    product_key: str,
    device_name: str,
    payload: HttpPropertyPost,
    db: Session = Depends(get_db),
) -> dict:
    result = ingest_property_payload(db, product_key, device_name, payload.params)
    if not result["accepted"]:
        raise HTTPException(status_code=400, detail=result)
    return {"code": 200, "message": "success", "data": result}


@app.post("/api/agent")
def agent(payload: AgentRequest, db: Session = Depends(get_db)) -> dict:
    return answer_agent_message(db, payload.message)


def _category_dict(row: Category) -> dict:
    return {"id": row.id, "name": row.name, "industry": row.industry, "scene": row.scene}


def _product_dict(row: Product) -> dict:
    return {
        "id": row.id,
        "category_id": row.category_id,
        "product_key": row.product_key,
        "name": row.name,
        "protocol": row.protocol,
        "status": row.status,
    }


def _device_dict(row: Device) -> dict:
    return {
        "id": row.id,
        "product_id": row.product_id,
        "device_name": row.device_name,
        "unique_no": row.unique_no,
        "status": row.status,
        "last_online_at": row.last_online_at,
        "last_report_at": row.last_report_at,
        "latest_properties": row.latest_properties or {},
    }


def _thing_model_dict(row: ThingModel) -> dict:
    return {
        "id": row.id,
        "product_id": row.product_id,
        "identifier": row.identifier,
        "name": row.name,
        "model_type": row.model_type,
        "data_type": row.data_type,
        "unit": row.unit,
        "access_mode": row.access_mode,
    }


def _rule_dict(row: Rule) -> dict:
    return {
        "id": row.id,
        "name": row.name,
        "product_id": row.product_id,
        "identifier": row.identifier,
        "operator": row.operator,
        "threshold": row.threshold,
        "message": row.message,
        "enabled": row.enabled,
    }


def _log_dict(row: DevicePropertyLog) -> dict:
    return {
        "id": row.id,
        "product_key": row.product_key,
        "device_name": row.device_name,
        "identifier": row.identifier,
        "value": row.value,
        "reported_at": row.reported_at,
    }


def _alarm_dict(row: AlarmLog) -> dict:
    return {
        "id": row.id,
        "rule_id": row.rule_id,
        "product_key": row.product_key,
        "device_name": row.device_name,
        "content": row.content,
        "triggered_at": row.triggered_at,
    }
