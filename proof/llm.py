"""Meta Model API client (OpenAI SDK, Chat Completions).

Verified facts (Decisions of 2026-10-26): base ``https://api.meta.ai/v1``,
``response_format: json_schema`` (strict) works, ``reasoning_effort`` works,
reasoning tokens count inside ``max_tokens`` so the default is generous.
"""
from __future__ import annotations

import json
import random
import re
import time
from typing import Any

from pydantic import BaseModel

from proof.config import Settings, compute_cost_from_usage, extract_usage_fields, get_pricing, load_settings
from proof.ledger import Ledger

DEFAULT_MAX_TOKENS = 8192
MAX_ATTEMPTS = 3


class LLMError(RuntimeError):
    """Base typed error for LLM failures."""


class InvalidJSONError(LLMError):
    """Response was not valid JSON even after the single repair call."""


class TruncatedResponseError(LLMError):
    """finish_reason == 'length' with empty content (reasoning ate the budget)."""


class ContributorGuardError(LLMError):
    """External code must never be sent to a -contributor model."""


def _is_external(metadata: dict[str, Any] | None) -> bool:
    if not metadata:
        return False
    if metadata.get("external_code") or metadata.get("contains_external_code"):
        return True
    if metadata.get("external"):
        return True
    if str(metadata.get("origin", "")).lower() == "external":
        return True
    if str(metadata.get("source", "")).lower() == "external":
        return True
    return False


def _resolve_schema(schema: Any) -> tuple[str, dict[str, Any], type[BaseModel] | None]:
    """Return (name, json_schema, pydantic_model_or_None) for *schema*."""
    if isinstance(schema, type) and issubclass(schema, BaseModel):
        return schema.__name__, schema.model_json_schema(), schema
    if isinstance(schema, BaseModel):
        cls = type(schema)
        return cls.__name__, cls.model_json_schema(), cls
    if isinstance(schema, dict):
        # {"name": ..., "schema": {...}} form.
        if "schema" in schema and isinstance(schema["schema"], dict):
            name = str(schema.get("name") or schema["schema"].get("title") or "response")
            return _sanitize_name(name), schema["schema"], None
        # {"json_schema": {"name":..., "schema":...}} form.
        if "json_schema" in schema and isinstance(schema["json_schema"], dict):
            inner = schema["json_schema"]
            if "schema" in inner and isinstance(inner["schema"], dict):
                name = str(inner.get("name") or inner["schema"].get("title") or "response")
                return _sanitize_name(name), inner["schema"], None
        name = str(schema.get("title") or "response")
        return _sanitize_name(name), schema, None
    raise LLMError(f"Unsupported schema type: {type(schema).__name__}")


def _sanitize_name(name: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_-]", "_", name)
    return cleaned or "response"


def _parse_content(content: str, pydantic_model: type[BaseModel] | None) -> Any:
    data = json.loads(content)
    if pydantic_model is not None:
        return pydantic_model.model_validate(data)
    return data


def _retry_after_seconds(exc: BaseException) -> float | None:
    # OpenAI SDK errors expose response headers; tests use plain attributes.
    response = getattr(exc, "response", None)
    headers = getattr(response, "headers", None) if response is not None else None
    if headers is not None:
        try:
            value = headers.get("retry-after") or headers.get("Retry-After")
        except Exception:
            value = None
        if value:
            try:
                return float(value)
            except (TypeError, ValueError):
                pass
    value = getattr(exc, "retry_after", None)
    if value is not None:
        try:
            return float(value)
        except (TypeError, ValueError):
            pass
    return None


def _is_retryable(exc: BaseException) -> bool:
    status = getattr(exc, "status_code", None)
    if status is None:
        status = getattr(exc, "status", None)
    if status is not None:
        try:
            code = int(status)
        except (TypeError, ValueError):
            code = -1
        if code == 429 or 500 <= code <= 599:
            return True
        return False
    name = exc.__class__.__name__.lower()
    if "timeout" in name or "timedout" in name:
        return True
    if "ratelimit" in name or "rate_limit" in name:
        return True
    # httpx / generic timeouts surface as TimeoutError subclasses.
    if isinstance(exc, TimeoutError):
        return True
    return False


class LLMClient:
    """Chat Completions client with retries, JSON-schema parsing and ledger."""

    def __init__(
        self,
        *,
        client: Any = None,
        ledger: Ledger | None = None,
        settings: Settings | None = None,
        sleep: Any = None,
    ) -> None:
        self._settings = settings or load_settings()
        self._ledger = ledger if ledger is not None else Ledger(settings=self._settings)
        self._sleep = sleep or time.sleep
        if client is not None:
            self._client = client
        else:
            from openai import OpenAI

            self._client = OpenAI(
                base_url=self._settings.base_url,
                api_key=self._settings.api_key,
            )

    @property
    def ledger(self) -> Ledger:
        return self._ledger

    @property
    def settings(self) -> Settings:
        return self._settings

    def _call_with_retries(self, kwargs: dict[str, Any]) -> Any:
        last_exc: BaseException | None = None
        for attempt in range(MAX_ATTEMPTS):
            try:
                return self._client.chat.completions.create(**kwargs)
            except Exception as exc:  # noqa: BLE001 - re-raised when not retryable
                last_exc = exc
                if not _is_retryable(exc) or attempt == MAX_ATTEMPTS - 1:
                    raise
                delay = _retry_after_seconds(exc)
                if delay is None:
                    delay = (2**attempt) * 0.5 + random.uniform(0, 0.3)
                self._sleep(delay)
        # Unreachable, but keeps type checkers happy.
        raise LLMError(f"LLM call failed: {last_exc}") from last_exc

    def _record(self, *, run_id: str | None, role: str, model: str, effort: str | None, usage: Any) -> float:
        fields = extract_usage_fields(usage)
        usd = compute_cost_from_usage(model, usage)
        self._ledger.record_call(
            run_id=run_id,
            role=role,
            model=model,
            effort=effort,
            input_tokens=fields["input_tokens"],
            cached_tokens=fields["cached_tokens"],
            output_tokens=fields["output_tokens"],
            reasoning_tokens=fields["reasoning_tokens"],
            usd=usd,
        )
        return usd

    def complete(
        self,
        role: str,
        messages: list[dict[str, Any]],
        *,
        model: str | None = None,
        effort: str | None = None,
        schema: Any = None,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        run_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Any:
        """Run one Chat Completion.

        When *schema* (a pydantic model or a JSON-schema dict) is given the
        call uses ``response_format`` json_schema strict mode and the parsed
        object is returned (a pydantic instance, or a dict for dict schemas).
        Without a schema the raw content string is returned.

        On invalid JSON exactly one repair call is made; if that also fails
        an :class:`InvalidJSONError` is raised. ``finish_reason == "length"``
        with empty content raises :class:`TruncatedResponseError`.
        """
        resolved_model = model or self._settings.model_for_role(role)
        resolved_effort = effort if effort is not None else self._settings.effort_for_role(role)

        # Refuse unknown models before any network call.
        get_pricing(resolved_model)

        # Never send external users' code to a -contributor model.
        if _is_external(metadata) and resolved_model.endswith("-contributor"):
            raise ContributorGuardError(
                f"Refusing to send external code to contributor model "
                f"{resolved_model!r}; use the standard model for external code"
            )

        # Hard caps are enforced BEFORE the call.
        self._ledger.check_caps(run_id)

        schema_name: str | None = None
        json_schema: dict[str, Any] | None = None
        pydantic_model: type[BaseModel] | None = None
        if schema is not None:
            schema_name, json_schema, pydantic_model = _resolve_schema(schema)

        kwargs: dict[str, Any] = {
            "model": resolved_model,
            "messages": messages,
            "max_tokens": max_tokens,
        }
        if resolved_effort:
            kwargs["reasoning_effort"] = resolved_effort
        if schema is not None:
            kwargs["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": schema_name,
                    "strict": True,
                    "schema": json_schema,
                },
            }

        response = self._call_with_retries(kwargs)
        content, finish_reason = self._extract_content(response)
        self._record(
            run_id=run_id, role=role, model=resolved_model,
            effort=resolved_effort, usage=getattr(response, "usage", None),
        )

        if finish_reason == "length" and not (content or "").strip():
            raise TruncatedResponseError(
                "Model returned finish_reason='length' with empty content; "
                "reasoning tokens count inside max_tokens, increase max_tokens"
            )

        if schema is None:
            return content

        try:
            return _parse_content(content or "", pydantic_model)
        except Exception as parse_error:
            # Exactly one repair call that sends the parse error back.
            repair_messages = list(messages) + [
                {"role": "assistant", "content": content or ""},
                {
                    "role": "user",
                    "content": (
                        "Your previous response was not valid JSON for the "
                        f"requested schema: {parse_error}. "
                        "Return only a valid JSON object matching the schema, "
                        "with no extra text."
                    ),
                },
            ]
            repair_kwargs = dict(kwargs)
            repair_kwargs["messages"] = repair_messages
            # Re-check caps before the repair call as well.
            self._ledger.check_caps(run_id)
            repair_response = self._call_with_retries(repair_kwargs)
            repair_content, repair_finish = self._extract_content(repair_response)
            self._record(
                run_id=run_id, role=role, model=resolved_model,
                effort=resolved_effort,
                usage=getattr(repair_response, "usage", None),
            )
            if repair_finish == "length" and not (repair_content or "").strip():
                raise TruncatedResponseError(
                    "Repair call returned finish_reason='length' with empty content"
                )
            try:
                return _parse_content(repair_content or "", pydantic_model)
            except Exception as repair_error:
                raise InvalidJSONError(
                    f"Response was not valid JSON after one repair attempt: "
                    f"{repair_error} (original error: {parse_error})"
                ) from repair_error

    @staticmethod
    def _extract_content(response: Any) -> tuple[str | None, str | None]:
        choices = getattr(response, "choices", None)
        if choices is None and isinstance(response, dict):
            choices = response.get("choices")
        if not choices:
            return None, None
        first = choices[0]
        if isinstance(first, dict):
            message = first.get("message") or {}
            content = message.get("content") if isinstance(message, dict) else None
            return content, first.get("finish_reason")
        message = getattr(first, "message", None)
        content = getattr(message, "content", None) if message is not None else None
        return content, getattr(first, "finish_reason", None)
