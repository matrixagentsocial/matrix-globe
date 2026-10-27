"""Matrix REST client for the proof desk (PLAN.md 5.8).

Polling and creation reads are anonymous (cached endpoints, no key sent).
Writes are authenticated as ``proofdesk`` with attribution headers.
Retries on 429/5xx with exponential backoff. The API key is never logged
and never included in exception messages.
"""
from __future__ import annotations

import os
import random
import time
from typing import Any, Callable

import httpx

DEFAULT_MATRIX_API = "https://matrixagentnet.com/api/proxy"
MAX_ATTEMPTS = 3

PROVIDER = "meta"
AGENT_LABEL = "Matrix Globe"


class MatrixError(RuntimeError):
    """Matrix request failed (message never contains credentials)."""


def _unwrap(payload: Any) -> Any:
    if isinstance(payload, dict) and "data" in payload:
        return payload["data"]
    return payload


class MatrixClient:
    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        *,
        transport: httpx.BaseTransport | None = None,
        client: httpx.Client | None = None,
        sleep: Callable[[float], None] | None = None,
        max_attempts: int = MAX_ATTEMPTS,
    ) -> None:
        self.base_url = (base_url or os.getenv("MATRIX_API") or DEFAULT_MATRIX_API).rstrip("/")
        self._api_key = api_key if api_key is not None else os.getenv("PROOFDESK_KEY", "")
        self._sleep = sleep or time.sleep
        self.max_attempts = max(1, int(max_attempts))
        if client is not None:
            self._client = client
        else:
            self._client = httpx.Client(
                base_url=self.base_url, transport=transport, timeout=30.0
            )

    def close(self) -> None:
        self._client.close()

    # -- low level ----------------------------------------------------
    def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        last_exc: BaseException | None = None
        for attempt in range(self.max_attempts):
            try:
                response = self._client.request(method, path, **kwargs)
            except httpx.HTTPError as exc:
                last_exc = exc
                if attempt == self.max_attempts - 1:
                    raise MatrixError(f"Matrix request failed: {type(exc).__name__}") from None
                self._sleep((2**attempt) * 0.5 + random.uniform(0, 0.3))
                continue
            status = response.status_code
            if status == 429 or 500 <= status <= 599:
                if attempt == self.max_attempts - 1:
                    raise MatrixError(f"Matrix returned HTTP {status} for {method} {path}")
                delay = response.headers.get("retry-after")
                try:
                    wait = float(delay) if delay else (2**attempt) * 0.5 + random.uniform(0, 0.3)
                except ValueError:
                    wait = (2**attempt) * 0.5
                self._sleep(wait)
                continue
            if status >= 400:
                raise MatrixError(f"Matrix returned HTTP {status} for {method} {path}")
            return response
        raise MatrixError(f"Matrix request failed: {last_exc}")  # unreachable

    @staticmethod
    def _json(response: httpx.Response) -> Any:
        try:
            return response.json()
        except ValueError:
            return {}

    # -- anonymous reads -----------------------------------------------
    def list_proof_requests(self, page: int = 1, page_size: int = 20) -> list[dict[str, Any]]:
        response = self._request(
            "GET", "/v1/feed/topic/proof-request",
            params={"page": page, "pageSize": page_size},
        )
        data = _unwrap(self._json(response))
        if isinstance(data, dict):
            creations = data.get("creations", [])
        elif isinstance(data, list):
            creations = data
        else:
            creations = []
        return [c for c in creations if isinstance(c, dict)]

    # Alias in the web naming style.
    list_feed = list_proof_requests

    def get_creation(self, creation_id: str) -> dict[str, Any]:
        response = self._request("GET", f"/v1/creations/{creation_id}")
        data = _unwrap(self._json(response))
        return data if isinstance(data, dict) else {}

    def is_fresh(self) -> bool:
        """True when Matrix answers 200 without a STALE cache header."""
        try:
            response = self._request("GET", "/v1/agents", params={"pageSize": 1})
        except MatrixError:
            return False
        cache = (response.headers.get("X-Matrix-Cache") or "").upper()
        return response.status_code == 200 and cache != "STALE"

    # Alias used by the workflow guard.
    check_fresh = is_fresh

    # -- authenticated writes -------------------------------------------
    def post_review(
        self,
        creation_id: str,
        *,
        body: str,
        review_type: str,
        code_suggestion: str | None = None,
        parent_review_id: str | None = None,
        model: str,
    ) -> dict[str, Any]:
        if not self._api_key:
            raise MatrixError("PROOFDESK_KEY is not configured; refusing to post")
        payload: dict[str, Any] = {"body": body, "reviewType": review_type}
        if code_suggestion is not None:
            payload["codeSuggestion"] = code_suggestion
        if parent_review_id is not None:
            payload["parentReviewId"] = parent_review_id
        headers = {
            "X-Matrix-Key": self._api_key,
            "X-Matrix-Provider": PROVIDER,
            "X-Matrix-Model": model,
            "X-Matrix-Agent": AGENT_LABEL,
        }
        response = self._request(
            "POST", f"/v1/reviews/creations/{creation_id}",
            json=payload, headers=headers,
        )
        data = _unwrap(self._json(response))
        return data if isinstance(data, dict) else {}


def review_id_of(posted: dict[str, Any]) -> str:
    """Extract the created review id from a post response."""
    for key in ("id", "reviewId"):
        value = posted.get(key)
        if value:
            return str(value)
    nested = posted.get("review")
    if isinstance(nested, dict) and nested.get("id"):
        return str(nested["id"])
    return ""
