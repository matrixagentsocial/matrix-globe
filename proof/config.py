"""Configuration, pricing and cost maths for Matrix Globe.

Settings are loaded from ``.env`` with python-dotenv. The pricing table is
the one verified in PLAN.md "Decisions of 2026-10-26" (source: Meta docs
``dev.meta.ai/docs/models`` and ``/docs/pricing-rate-limits``, verified live
2026-10-26). All prices are USD per 1M tokens as
``input / cached_input / output``. Reasoning tokens bill as output and are
already included in ``completion_tokens``.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

load_dotenv()


class UnknownModelError(ValueError):
    """Raised when a model id has no entry in the PRICING table."""


@dataclass(frozen=True)
class Pricing:
    input: float
    cached_input: float
    output: float


# USD per 1M tokens (input / cached input / output), per Decisions of 2026-10-26.
# Spark 1.1 and 1.2 are not priced separately in the Decisions section; they
# share the Spark family list price below until Meta publishes a distinct rate.
PRICING: dict[str, Pricing] = {
    "muse-wonder-1.0": Pricing(input=4.00, cached_input=0.20, output=20.00),
    "muse-spark-1.3": Pricing(input=1.25, cached_input=0.15, output=4.25),
    "muse-spark-1.3-contributor": Pricing(input=0.10, cached_input=0.002, output=0.20),
    "muse-spark-1.2": Pricing(input=1.25, cached_input=0.15, output=4.25),
    "muse-spark-1.2-contributor": Pricing(input=0.10, cached_input=0.002, output=0.20),
    "muse-spark-1.1": Pricing(input=1.25, cached_input=0.15, output=4.25),
    # Baseten Muse Spark Open: $1.25/$0.15/$4.25 per 1M (baseten.co/library/muse-spark-open).
    "meta-models/muse-spark-open-1026": Pricing(input=1.25, cached_input=0.15, output=4.25),
}

OPEN_MODEL = "meta-models/muse-spark-open-1026"
BASETEN_BASE_URL = "https://inference.baseten.co/v1"
BASETEN_MODEL_PREFIX = "meta-models/"


def provider_for_model(model: str) -> str:
    """Provider for *model*: ids starting with ``meta-models/`` go to Baseten."""
    return "baseten" if str(model or "").startswith(BASETEN_MODEL_PREFIX) else "meta"


def get_pricing(model: str) -> Pricing:
    """Return pricing for *model* or raise a clear error for unknown ids."""
    try:
        return PRICING[model]
    except KeyError:
        known = ", ".join(sorted(PRICING))
        raise UnknownModelError(
            f"Unknown model id {model!r}: no pricing entry. Known models: {known}"
        ) from None


def compute_cost(
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    cached_tokens: int = 0,
) -> float:
    """Compute USD for one call.

    Cached prompt tokens bill at the cached rate; the rest of the prompt
    bills at the input rate. ``completion_tokens`` already includes
    reasoning tokens, so output bills ``completion_tokens`` at the output
    rate with no extra charge.
    """
    pricing = get_pricing(model)
    prompt_tokens = max(int(prompt_tokens or 0), 0)
    completion_tokens = max(int(completion_tokens or 0), 0)
    cached_tokens = max(int(cached_tokens or 0), 0)
    cached_tokens = min(cached_tokens, prompt_tokens)
    non_cached = prompt_tokens - cached_tokens
    usd = (
        non_cached * pricing.input
        + cached_tokens * pricing.cached_input
        + completion_tokens * pricing.output
    ) / 1_000_000
    return usd


def _usage_get(usage: Any, *names: str) -> Any:
    """Read the first present field from a usage object or dict."""
    if usage is None:
        return None
    if isinstance(usage, dict):
        for name in names:
            if name in usage and usage[name] is not None:
                return usage[name]
        return None
    for name in names:
        value = getattr(usage, name, None)
        if value is not None:
            return value
    return None


def _detail_get(details: Any, *names: str) -> Any:
    if details is None:
        return None
    if isinstance(details, dict):
        for name in names:
            if name in details and details[name] is not None:
                return details[name]
        return None
    for name in names:
        value = getattr(details, name, None)
        if value is not None:
            return value
    return None


def compute_cost_from_usage(model: str, usage: Any) -> float:
    """Compute USD from an OpenAI-style usage object.

    Accepts SDK objects, pydantic models or plain dicts. Reasoning tokens
    are already inside ``completion_tokens`` and are not billed twice.
    """
    prompt_tokens = _usage_get(usage, "prompt_tokens", "input_tokens") or 0
    completion_tokens = _usage_get(usage, "completion_tokens", "output_tokens") or 0
    prompt_details = _usage_get(usage, "prompt_tokens_details", "input_tokens_details")
    cached_tokens = _detail_get(prompt_details, "cached_tokens", "cached_input_tokens") or 0
    return compute_cost(model, int(prompt_tokens), int(completion_tokens), int(cached_tokens))


def extract_usage_fields(usage: Any) -> dict[str, int]:
    """Normalise a usage object into ledger token fields."""
    prompt_tokens = _usage_get(usage, "prompt_tokens", "input_tokens") or 0
    completion_tokens = _usage_get(usage, "completion_tokens", "output_tokens") or 0
    prompt_details = _usage_get(usage, "prompt_tokens_details", "input_tokens_details")
    cached_tokens = _detail_get(prompt_details, "cached_tokens", "cached_input_tokens") or 0
    completion_details = _usage_get(
        usage, "completion_tokens_details", "output_tokens_details"
    )
    reasoning_tokens = _detail_get(completion_details, "reasoning_tokens") or 0
    if not reasoning_tokens:
        direct = _usage_get(usage, "reasoning_tokens")
        if direct:
            reasoning_tokens = direct
    return {
        "input_tokens": int(prompt_tokens),
        "cached_tokens": int(cached_tokens),
        "output_tokens": int(completion_tokens),
        "reasoning_tokens": int(reasoning_tokens),
    }


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    return float(raw)


@dataclass
class Settings:
    base_url: str
    api_key: str
    model_builder: str
    model_builder_external: str
    model_reviewer: str
    max_usd_total: float
    max_usd_per_run: float

    baseten_base_url: str = BASETEN_BASE_URL
    baseten_api_key: str = ""
    baseten_max_usd: float = 90.0
    model_open: str = OPEN_MODEL
    desk_stack: str = ""

    # Efforts per role (Decisions of 2026-10-26; configurable).
    effort_builder: str = "medium"
    effort_reviewer: str = "high"
    effort_reviser: str = "medium"
    effort_self_refine: str = "medium"

    @property
    def role_models(self) -> dict[str, str]:
        return {
            "builder": self.model_builder,
            "builder_external": self.model_builder_external,
            "reviewer": self.model_reviewer,
            "reviser": self.model_builder,
            "self_refine": self.model_builder,
            "freeform_reviewer": self.model_reviewer,
        }

    @property
    def role_efforts(self) -> dict[str, str]:
        return {
            "builder": self.effort_builder,
            "builder_external": self.effort_builder,
            "reviewer": self.effort_reviewer,
            "reviser": self.effort_reviser,
            "self_refine": self.effort_self_refine,
            "freeform_reviewer": self.effort_reviewer,
        }

    def model_for_role(self, role: str) -> str:
        return self.role_models.get(role, self.model_builder)

    def effort_for_role(self, role: str) -> str:
        return self.role_efforts.get(role, self.effort_builder)


def load_settings(env_file: str | Path | None = None) -> Settings:
    if env_file is not None:
        load_dotenv(env_file, override=True)
    else:
        load_dotenv()
    return Settings(
        base_url=os.getenv("META_BASE_URL", "https://api.meta.ai/v1"),
        api_key=os.getenv("MODEL_API_KEY", ""),
        model_builder=os.getenv("MODEL_BUILDER", "muse-spark-1.3-contributor"),
        model_builder_external=os.getenv(
            "MODEL_BUILDER_EXTERNAL", "muse-spark-1.3"
        ),
        model_reviewer=os.getenv("MODEL_REVIEWER", "muse-wonder-1.0"),
        max_usd_total=_env_float("MAX_USD_TOTAL", 100.0),
        max_usd_per_run=_env_float("MAX_USD_PER_RUN", 0.60),
        baseten_base_url=os.getenv("BASETEN_BASE_URL", BASETEN_BASE_URL),
        baseten_api_key=os.getenv("BASETEN_API_KEY", ""),
        baseten_max_usd=_env_float("BASETEN_MAX_USD", 90.0),
        model_open=os.getenv("MODEL_OPEN", OPEN_MODEL),
        desk_stack=os.getenv("DESK_STACK", ""),
        effort_builder=os.getenv("EFFORT_BUILDER", "medium"),
        effort_reviewer=os.getenv("EFFORT_REVIEWER", "high"),
        effort_reviser=os.getenv("EFFORT_REVISER", "medium"),
        effort_self_refine=os.getenv("EFFORT_SELF_REFINE", "medium"),
    )


# Default settings loaded at import time.
settings = load_settings()
