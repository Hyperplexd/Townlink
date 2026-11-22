import base64
from typing import Any, Optional, Type, TypeVar
import httpx
from pydantic import BaseModel
from google import genai
from google.genai import types
from config import active_llm_provider, reasoning_model_name, settings, vision_model_name

T = TypeVar("T", bound=BaseModel)


def _strip_unsupported_schema_defaults(node: Any) -> None:
    """Adapt Pydantic JSON Schema to Gemini response schemas.

    Gemini rejects non-null defaults, and its Type enum has no null.
    Optional fields arrive as anyOf [T, {"type": "null"}]; collapse those
    to the inner schema plus nullable=true.
    """
    if isinstance(node, dict):
        if node.get("default") is not None:
            node.pop("default")
        any_of = node.get("anyOf")
        if isinstance(any_of, list):
            non_null = [
                item
                for item in any_of
                if not (isinstance(item, dict) and item.get("type") == "null")
            ]
            if len(non_null) != len(any_of):
                if len(non_null) == 1 and isinstance(non_null[0], dict):
                    node.pop("anyOf")
                    for key, value in non_null[0].items():
                        node.setdefault(key, value)
                else:
                    node["anyOf"] = non_null
                node["nullable"] = True
        schema_type = node.get("type")
        if isinstance(schema_type, list) and "null" in schema_type:
            rest = [item for item in schema_type if item != "null"]
            node["nullable"] = True
            if len(rest) == 1:
                node["type"] = rest[0]
            elif rest:
                node["type"] = rest
            else:
                node.pop("type", None)
        for value in node.values():
            _strip_unsupported_schema_defaults(value)
    elif isinstance(node, list):
        for item in node:
            _strip_unsupported_schema_defaults(item)


class BaseCivicAgent:
    def __init__(self, agent_number: int, agent_id: str, agent_name_el: str) -> None:
        self.agent_number = agent_number
        self.agent_id = agent_id
        self.agent_name_el = agent_name_el
        self._client: Optional[genai.Client] = None
        self._gemini_key: Optional[str] = None

    @property
    def client(self) -> genai.Client:
        key = (settings.GEMINI_API_KEY or "").strip()
        if not key:
            raise RuntimeError("GEMINI_API_KEY is not set.")
        if self._client is None or self._gemini_key != key:
            self._client = genai.Client(api_key=key)
            self._gemini_key = key
        return self._client

    def set_api_key(self, api_key: str) -> None:
        key = (api_key or "").strip()
        if not key:
            return
        if active_llm_provider() == "openrouter":
            settings.OPENROUTER_API_KEY = key
            return
        settings.GEMINI_API_KEY = key

    async def generate_structured(
        self,
        prompt: str,
        response_schema: Type[T],
        system_instruction: str,
        image_bytes: Optional[bytes] = None,
        image_mime_type: str = "image/jpeg",
        model_name: Optional[str] = None,
        temperature: float = 0.15,
    ) -> T:
        if active_llm_provider() == "openrouter":
            return await self._generate_openrouter(
                prompt,
                response_schema,
                system_instruction,
                image_bytes,
                image_mime_type,
                model_name,
                temperature,
            )

        target_model = model_name or (vision_model_name() if image_bytes else reasoning_model_name())
        contents: list[Any] = []
        if image_bytes:
            contents.append(types.Part.from_bytes(data=image_bytes, mime_type=image_mime_type))
        contents.append(prompt)

        schema = response_schema.model_json_schema()
        _strip_unsupported_schema_defaults(schema)

        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            response_mime_type="application/json",
            response_schema=schema,
            temperature=temperature,
        )

        response = await self.client.aio.models.generate_content(
            model=target_model,
            contents=contents,
            config=config,
        )

        if response.parsed is not None and isinstance(response.parsed, response_schema):
            return response.parsed
        return response_schema.model_validate_json(response.text)

    async def _generate_openrouter(
        self,
        prompt: str,
        response_schema: Type[T],
        system_instruction: str,
        image_bytes: Optional[bytes],
        image_mime_type: str,
        model_name: Optional[str],
        temperature: float,
    ) -> T:
        key = (settings.OPENROUTER_API_KEY or "").strip()
        if not key:
            raise RuntimeError("OPENROUTER_API_KEY is not set.")
        if key.startswith("gsk_"):
            raise RuntimeError("Το OPENROUTER_API_KEY είναι κλειδί Groq (gsk_). Χρειάζεται κλειδί OpenRouter (sk-or-).")
        target_model = model_name or (vision_model_name() if image_bytes else reasoning_model_name())
        user_content: list[dict[str, Any]] = []
        if image_bytes:
            encoded = base64.b64encode(image_bytes).decode("ascii")
            mime = image_mime_type or "image/jpeg"
            user_content.append({
                "type": "image_url",
                "image_url": {"url": f"data:{mime};base64,{encoded}"},
            })
        user_content.append({"type": "text", "text": prompt})

        schema = response_schema.model_json_schema()
        schema.pop("$schema", None)
        body = {
            "model": target_model,
            "temperature": temperature,
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_content},
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": response_schema.__name__,
                    "strict": False,
                    "schema": schema,
                },
            },
        }
        url = f"{settings.OPENROUTER_API_BASE.rstrip('/')}/chat/completions"
        async with httpx.AsyncClient(timeout=180.0) as http:
            response = await http.post(
                url,
                headers={
                    "Authorization": f"Bearer {key}",
                    "HTTP-Referer": "http://localhost:5173",
                    "X-Title": "TownLink",
                },
                json=body,
            )
        if response.status_code >= 400:
            detail = response.text[:500]
            raise RuntimeError(f"OpenRouter API {response.status_code}: {detail}")
        payload = response.json()
        try:
            text = _openrouter_message_text(payload["choices"][0]["message"])
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError("OpenRouter API returned no message content.") from exc
        if not text:
            raise RuntimeError("OpenRouter API returned an empty response.")
        return response_schema.model_validate_json(_strip_json_fence(text))


def _openrouter_message_text(message: Any) -> str:
    content = message.get("content") if isinstance(message, dict) else None
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                parts.append(str(item.get("text") or item.get("content") or ""))
        return "".join(parts)
    return ""


def _strip_json_fence(text: str) -> str:
    raw = text.strip()
    if not raw.startswith("```"):
        return raw
    lines = raw.splitlines()
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines).strip()
