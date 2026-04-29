import json, time, logging, os
from typing import Optional
import httpx
from sqlalchemy.orm import Session
from app.models.model_config import ModelConfig
from app.models.usage import ApiUsageLog
from app.config import settings

logger = logging.getLogger(__name__)

class LLMClient:
    def __init__(self, model_config: ModelConfig):
        self.base_url = model_config.base_url.rstrip("/")
        self.api_key = model_config.api_key
        self.model = model_config.model
        self.temperature = model_config.temperature
        self.max_tokens = model_config.max_tokens

    def _call_api(self, messages: list[dict], response_format: Optional[dict] = None) -> tuple[str, dict]:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        body = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        if response_format:
            body["response_format"] = response_format

        start = time.time()
        try:
            with httpx.Client(timeout=settings.request_timeout_seconds) as client:
                resp = client.post(f"{self.base_url}/chat/completions", json=body, headers=headers)
            latency = int((time.time() - start) * 1000)
            resp.raise_for_status()
            data = resp.json()
            choice = data["choices"][0]
            content = choice["message"]["content"]
            usage = data.get("usage", {})
            return content, {
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
                "model": self.model,
                "latency_ms": latency,
            }
        except httpx.TimeoutException:
            raise TimeoutError(f"API request timed out after {settings.request_timeout_seconds}s")
        except Exception as e:
            latency = int((time.time() - start) * 1000)
            raise RuntimeError(f"API call failed: {str(e)}")

    def generate_text(self, system_prompt: str, user_prompt: str) -> str:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        content, _ = self._call_api(messages)
        return content

    def generate_json(self, system_prompt: str, user_prompt: str) -> dict:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        content, _ = self._call_api(messages, response_format={"type": "json_object"})
        try:
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].strip()
            return json.loads(content)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON: {e}")

    @staticmethod
    def get_default_client(db: Session) -> "LLMClient":
        config = db.query(ModelConfig).filter(ModelConfig.is_default == True).first()
        if not config:
            raise ValueError("No default model configured. Please add a model in Settings.")
        return LLMClient(config)

    @staticmethod
    def record_usage(db: Session, project_id: str, job_id: str, usage_info: dict, success: bool, error_message: str = ""):
        log = ApiUsageLog(
            project_id=project_id,
            job_id=job_id,
            model=usage_info.get("model", "unknown"),
            prompt_tokens=usage_info.get("prompt_tokens", 0),
            completion_tokens=usage_info.get("completion_tokens", 0),
            total_tokens=usage_info.get("total_tokens", 0),
            estimated_cost=0.0,
            latency_ms=usage_info.get("latency_ms", 0),
            success=success,
            error_message=error_message
        )
        db.add(log)
        db.commit()