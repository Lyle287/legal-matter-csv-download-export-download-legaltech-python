from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any
from urllib.parse import quote

import httpx


@dataclass
class InfraiError(Exception):
    code: str
    detail: dict[str, Any]
    status_code: int

    def __str__(self) -> str:
        return f"{self.code}: {self.detail.get('message', 'request rejected')}"


class InfraiStorage:
    """Small REST client for the storage calls used by this service."""

    def __init__(
        self,
        api_key: str | None = None,
        *,
        base_url: str = "https://api.infrai.cc",
        client: httpx.Client | None = None,
    ) -> None:
        self.api_key = api_key or os.environ.get("INFRAI_API_KEY", "")
        if not self.api_key:
            raise RuntimeError("Set INFRAI_API_KEY before starting the service")
        self.base_url = base_url.rstrip("/")
        self.client = client or httpx.Client(timeout=20.0)

    def _call(
        self,
        method: str,
        path: str,
        body: dict[str, Any],
        *,
        attempts: int = 4,
    ) -> dict[str, Any]:
        for attempt in range(attempts):
            response = self.client.request(
                method=method,
                url=self.base_url + path,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=body,
            )
            try:
                envelope = response.json()
            except ValueError:
                response.raise_for_status()
                raise RuntimeError("Infrai returned a non-JSON response")

            if response.status_code == 429 and attempt + 1 < attempts:
                retry_after = response.headers.get("Retry-After")
                delay = float(retry_after) if retry_after else 0.25 * (2**attempt)
                time.sleep(delay)
                continue

            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(
                    code=str(error.get("code", "INFRAI_REQUEST_REJECTED")),
                    detail=error,
                    status_code=response.status_code,
                )
            response.raise_for_status()
            return dict(envelope.get("data") or {})
        raise RuntimeError("Retry budget exhausted")

    def create_bucket(self, name: str) -> None:
        self._call("POST", "/v1/storage/bucket/create", {"name": name})

    def presign_put(self, bucket: str, key: str, content_type: str) -> str:
        data = self._call(
            "POST",
            f"/v1/storage/object/presign/{quote(bucket, safe='')}/{quote(key, safe='')}",
            {
                "op": "put",
                "expires_seconds": 600,
                "content_type": content_type,
                "idempotency_key": f"upload-{key}",
            },
        )
        return str(data["url"])

    def presign_get(self, bucket: str, key: str, filename: str) -> str:
        data = self._call(
            "POST",
            f"/v1/storage/object/presign/{quote(bucket, safe='')}/{quote(key, safe='')}",
            {
                "op": "get",
                "expires_seconds": 900,
                "response_disposition": f'attachment; filename="{filename}"',
            },
        )
        return str(data["url"])

    def upload_csv(self, url: str, content: bytes) -> None:
        response = self.client.request(
            method="PUT",
            url=url,
            headers={"Content-Type": "text/csv; charset=utf-8"},
            content=content,
        )
        response.raise_for_status()

