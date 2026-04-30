from fastapi import APIRouter, Depends, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.model_config import ModelConfig
from app.services.llm_client import LLMClient
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/settings/models/add")
def add_model(
    name: str = Form(...),
    provider: str = Form(""),
    base_url: str = Form(...),
    api_key: str = Form(...),
    model: str = Form(...),
    temperature: float = Form(0.7),
    max_tokens: int = Form(4096),
    is_default: int = Form(0),
    db: Session = Depends(get_db)
):
    existing = db.query(ModelConfig).filter(ModelConfig.is_default == True).first()
    default_true = (is_default == 1 or not existing)
    
    if default_true:
        db.query(ModelConfig).update({"is_default": False})
    
    config = ModelConfig(
        name=name,
        provider=provider,
        base_url=base_url,
        api_key=api_key,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        is_default=default_true
    )
    db.add(config)
    db.commit()
    return RedirectResponse(url="/settings?success=模型添加成功", status_code=303)

@router.post("/settings/models/{model_id}/set-default")
def set_default(model_id: str, db: Session = Depends(get_db)):
    db.query(ModelConfig).update({"is_default": False})
    config = db.query(ModelConfig).filter(ModelConfig.id == model_id).first()
    if config:
        config.is_default = True
        db.commit()
    return RedirectResponse(url="/settings?success=已设为默认模型", status_code=303)

@router.post("/settings/models/{model_id}/delete")
def delete_model(model_id: str, db: Session = Depends(get_db)):
    config = db.query(ModelConfig).filter(ModelConfig.id == model_id).first()
    if config:
        db.delete(config)
        db.commit()
    return RedirectResponse(url="/settings", status_code=303)

@router.post("/settings/models/{model_id}/test")
def test_model(model_id: str, db: Session = Depends(get_db)):
    try:
        client = LLMClient.get_client_by_id(model_id, db)
        result = client.generate_text("你是一个助手", "请回复ok")
        return RedirectResponse(url=f"/settings?success=测试成功：{result[:100]}", status_code=303)
    except Exception as e:
        logger.error(f"Model test failed: {e}")
        return RedirectResponse(url=f"/settings?error=测试失败：{str(e)}", status_code=303)
