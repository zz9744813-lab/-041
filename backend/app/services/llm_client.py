import json
import time
import logging
from typing import Optional

import httpx
from sqlalchemy.orm import Session

from app.models import ModelConfig, GenerationJob, ApiUsageLog

logger = logging.getLogger(__name__)


class LLMClient:
    """OpenAI-compatible LLM client with usage logging."""

    def __init__(self, config: ModelConfig, db: Session, job: Optional[GenerationJob] = None):
        self.config = config
        self.db = db
        self.job = job

    def _log_usage(self, model: str, prompt_tokens: int, completion_tokens: int,
                   latency_ms: int, success: bool, error_message: str = ""):
        log = ApiUsageLog(
            model=model,
            job_id=self.job.id if self.job else None,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            latency_ms=latency_ms,
            success=success,
            error_message=error_message
        )
        self.db.add(log)
        self.db.commit()

    def generate_text(self, system_prompt: str, user_prompt: str,
                      temperature: Optional[float] = None) -> str:
        start = time.time()
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": temperature if temperature is not None else self.config.temperature,
            "max_tokens": self.config.max_tokens
        }
        try:
            with httpx.Client(timeout=120.0) as client:
                resp = client.post(
                    f"{self.config.base_url.rstrip('/')}/chat/completions",
                    headers=headers,
                    json=payload
                )
                resp.raise_for_status()
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                pt = data.get("usage", {}).get("prompt_tokens", 0)
                ct = data.get("usage", {}).get("completion_tokens", 0)
                latency = int((time.time() - start) * 1000)
                self._log_usage(self.config.model, pt, ct, latency, True)
                return content
        except Exception as e:
            latency = int((time.time() - start) * 1000)
            masked = str(e).replace(self.config.api_key, "***")
            self._log_usage(self.config.model, 0, 0, latency, False, masked)
            raise RuntimeError(f"LLM API call failed: {masked}")

    def generate_json(self, system_prompt: str, user_prompt: str,
                      temperature: Optional[float] = None) -> dict:
        text = self.generate_text(system_prompt, user_prompt, temperature)
        if "\`\`\`json" in text:
            text = text.split("\`\`\`json")[1].split("\`\`\`")[0].strip()
        elif "\`\`\`" in text:
            text = text.split("\`\`\`")[1].split("\`\`\`")[0].strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            logger.warning("Failed to parse JSON, trying lenient parse")
            start_idx = text.find("{")
            end_idx = text.rfind("}")
            if start_idx >= 0 and end_idx > start_idx:
                try:
                    return json.loads(text[start_idx:end_idx + 1])
                except json.JSONDecodeError:
                    pass
            return {"error": "JSON parse failed", "raw": text[:500]}


def get_default_model(db: Session) -> Optional[ModelConfig]:
    return db.query(ModelConfig).filter(ModelConfig.is_default == True).first()
