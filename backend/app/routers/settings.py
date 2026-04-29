from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import ModelConfig
from app.schemas import ModelConfigCreate, ModelConfigUpdate, ModelConfigResponse

router = APIRouter()

def _mask_key(key: str) -> str:
    if len(key) <= 8:
        return "***"
    return key[:4] + "..." + key[-4:]


@router.get("/model-configs", response_model=List[ModelConfigResponse])
def get_model_configs(db: Session = Depends(get_db)):
    configs = db.query(ModelConfig).order_by(ModelConfig.is_default.desc(), ModelConfig.created_at.desc()).all()
    result = []
    for c in configs:
        resp = ModelConfigResponse.model_validate(c)
        resp.api_key = _mask_key(c.api_key)
        result.append(resp)
    return result


@router.post("/model-configs", response_model=ModelConfigResponse, status_code=201)
def create_model_config(config: ModelConfigCreate, db: Session = Depends(get_db)):
    # If this is set as default, unset others
    if config.is_default:
        db.query(ModelConfig).filter(ModelConfig.is_default == True).update({"is_default": False})
    db_config = ModelConfig(**config.model_dump())
    db.add(db_config)
    db.commit()
    db.refresh(db_config)
    resp = ModelConfigResponse.model_validate(db_config)
    resp.api_key = _mask_key(db_config.api_key)
    return resp


@router.put("/model-configs/{config_id}", response_model=ModelConfigResponse)
def update_model_config(config_id: str, config_update: ModelConfigUpdate, db: Session = Depends(get_db)):
    db_config = db.query(ModelConfig).filter(ModelConfig.id == config_id).first()
    if not db_config:
        raise HTTPException(status_code=404, detail="Model config not found")
    update_data = config_update.model_dump(exclude_unset=True)
    if update_data.get("is_default"):
        db.query(ModelConfig).filter(ModelConfig.is_default == True, ModelConfig.id != config_id).update({"is_default": False})
    for field, value in update_data.items():
        setattr(db_config, field, value)
    db.commit()
    db.refresh(db_config)
    resp = ModelConfigResponse.model_validate(db_config)
    resp.api_key = _mask_key(db_config.api_key)
    return resp


@router.delete("/model-configs/{config_id}")
def delete_model_config(config_id: str, db: Session = Depends(get_db)):
    db_config = db.query(ModelConfig).filter(ModelConfig.id == config_id).first()
    if not db_config:
        raise HTTPException(status_code=404, detail="Model config not found")
    db.delete(db_config)
    db.commit()
    return {"message": "Model config deleted"}


@router.post("/model-configs/{config_id}/set-default", response_model=ModelConfigResponse)
def set_default_config(config_id: str, db: Session = Depends(get_db)):
    db_config = db.query(ModelConfig).filter(ModelConfig.id == config_id).first()
    if not db_config:
        raise HTTPException(status_code=404, detail="Model config not found")
    db.query(ModelConfig).filter(ModelConfig.is_default == True).update({"is_default": False})
    db_config.is_default = True
    db.commit()
    db.refresh(db_config)
    resp = ModelConfigResponse.model_validate(db_config)
    resp.api_key = _mask_key(db_config.api_key)
    return resp


@router.post("/model-configs/{config_id}/test")
def test_model_config(config_id: str, db: Session = Depends(get_db)):
    """Test model connection by sending a simple request."""
    from app.services.llm_client import LLMClient
    db_config = db.query(ModelConfig).filter(ModelConfig.id == config_id).first()
    if not db_config:
        raise HTTPException(status_code=404, detail="Model config not found")
    try:
        client = LLMClient(db_config, db)
        result = client.generate_text("你是一个助手", "回复'连接成功'这四个字", temperature=0.1)
        return {"success": True, "message": result.strip()}
    except Exception as e:
        return {"success": False, "message": str(e)}
