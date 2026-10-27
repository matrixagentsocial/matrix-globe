"""Append-only JSONL cost ledger with hard caps.

One line per LLM call:
``{ts, run_id, role, model, effort, input_tokens, cached_tokens,
output_tokens, reasoning_tokens, usd}``.

The ledger is the product-side source of truth for spend. ``check_caps``
must be called BEFORE a call; it raises :class:`HardCapExceeded` once the
total spend has reached ``MAX_USD_TOTAL`` or the run spend has reached
``MAX_USD_PER_RUN``.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from proof.config import Settings, load_settings, provider_for_model

# Anchored to the repo root so the ledger does not depend on the cwd.
DEFAULT_LEDGER_PATH = Path(__file__).resolve().parents[1] / "state" / "ledger.jsonl"


class HardCapExceeded(RuntimeError):
    """Raised before a call when a hard dollar cap has been reached."""


class Ledger:
    def __init__(
        self,
        path: str | Path = DEFAULT_LEDGER_PATH,
        settings: Settings | None = None,
    ) -> None:
        self.path = Path(path)
        self._settings = settings or load_settings()

    # -- writing ------------------------------------------------------
    def append(self, entry: dict[str, Any]) -> dict[str, Any]:
        """Append one call record and return the stored record."""
        provider = entry.get("provider") or provider_for_model(str(entry.get("model") or ""))
        record: dict[str, Any] = {
            "ts": entry.get("ts")
            or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "run_id": entry.get("run_id"),
            "role": entry.get("role"),
            "model": entry.get("model"),
            "provider": provider,
            "effort": entry.get("effort"),
            "input_tokens": int(entry.get("input_tokens", 0) or 0),
            "cached_tokens": int(entry.get("cached_tokens", 0) or 0),
            "output_tokens": int(entry.get("output_tokens", 0) or 0),
            "reasoning_tokens": int(entry.get("reasoning_tokens", 0) or 0),
            "usd": float(entry.get("usd", 0.0) or 0.0),
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
        return record

    def record_call(
        self,
        *,
        run_id: str | None,
        role: str,
        model: str,
        effort: str | None,
        input_tokens: int,
        cached_tokens: int,
        output_tokens: int,
        reasoning_tokens: int,
        usd: float,
        ts: str | None = None,
        provider: str | None = None,
    ) -> dict[str, Any]:
        return self.append(
            {
                "ts": ts,
                "run_id": run_id,
                "role": role,
                "model": model,
                "effort": effort,
                "input_tokens": input_tokens,
                "cached_tokens": cached_tokens,
                "output_tokens": output_tokens,
                "reasoning_tokens": reasoning_tokens,
                "usd": usd,
                "provider": provider or provider_for_model(model),
            }
        )

    # -- reading / totals ----------------------------------------------
    def entries(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        rows: list[dict[str, Any]] = []
        with self.path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                rows.append(json.loads(line))
        return rows

    def total_usd(self) -> float:
        return sum(float(row.get("usd", 0.0) or 0.0) for row in self.entries())

    def total_usd_by_provider(self, provider: str) -> float:
        total = 0.0
        for row in self.entries():
            row_provider = row.get("provider") or provider_for_model(str(row.get("model") or ""))
            if row_provider == provider:
                total += float(row.get("usd", 0.0) or 0.0)
        return total

    def run_usd(self, run_id: str | None) -> float:
        if run_id is None:
            return 0.0
        return sum(
            float(row.get("usd", 0.0) or 0.0)
            for row in self.entries()
            if row.get("run_id") == run_id
        )

    def totals(self) -> dict[str, float]:
        """Return ``{"total": ..., "<run_id>": ...}`` running totals."""
        result: dict[str, float] = {"total": self.total_usd()}
        for row in self.entries():
            run_id = row.get("run_id")
            if run_id is None:
                continue
            result[run_id] = result.get(run_id, 0.0) + float(row.get("usd", 0.0) or 0.0)
        return result

    # -- caps -----------------------------------------------------------
    def check_caps(
        self,
        run_id: str | None = None,
        *,
        max_usd_total: float | None = None,
        max_usd_per_run: float | None = None,
        provider: str | None = None,
        model: str | None = None,
        baseten_max_usd: float | None = None,
    ) -> None:
        """Raise :class:`HardCapExceeded` if either cap has been reached.

        Must be called BEFORE issuing a new API call. A spend exactly at
        the cap counts as reached (no further call is allowed).
        """
        cap_total = (
            self._settings.max_usd_total if max_usd_total is None else max_usd_total
        )
        cap_run = (
            self._settings.max_usd_per_run
            if max_usd_per_run is None
            else max_usd_per_run
        )
        resolved_provider = provider or (provider_for_model(model) if model else None)
        if resolved_provider == "baseten":
            cap_baseten = (
                getattr(self._settings, "baseten_max_usd", 90.0)
                if baseten_max_usd is None else baseten_max_usd
            )
            btotal = self.total_usd_by_provider("baseten")
            if btotal >= cap_baseten:
                raise HardCapExceeded(
                    f"Hard cap reached: Baseten spend ${btotal:.4f} >= "
                    f"BASETEN_MAX_USD ${cap_baseten:.4f}; refusing further calls"
                )
        elif resolved_provider == "meta":
            total = self.total_usd_by_provider("meta")
            if total >= cap_total:
                raise HardCapExceeded(
                    f"Hard cap reached: total spend ${total:.4f} >= "
                    f"MAX_USD_TOTAL ${cap_total:.4f}; refusing further calls"
                )
        else:
            total = self.total_usd()
            if total >= cap_total:
                raise HardCapExceeded(
                    f"Hard cap reached: total spend ${total:.4f} >= "
                    f"MAX_USD_TOTAL ${cap_total:.4f}; refusing further calls"
                )
        if run_id is not None:
            run_total = self.run_usd(run_id)
            if run_total >= cap_run:
                raise HardCapExceeded(
                    f"Hard cap reached: run {run_id!r} spend ${run_total:.4f} >= "
                    f"MAX_USD_PER_RUN ${cap_run:.4f}; refusing further calls"
                )
