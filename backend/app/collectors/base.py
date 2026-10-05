import hashlib
import json
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx


@dataclass(frozen=True)
class CapturedResponse:
    body: bytes
    request_url: str
    status_code: int
    content_type: str | None
    response_headers: dict[str, str]
    retry_count: int
    captured_at: datetime

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.body).hexdigest()

    def json(self) -> Any:
        return json.loads(self.body)


@dataclass(frozen=True)
class NormalizedJob:
    external_identity: str
    title: str
    company: str
    city: str
    requirements: str
    detail_url: str
    content_hash: str
    deadline_raw: str | None = None
    deadline_at: datetime | None = None
    recruitment_status: str | None = None
    explicit_closed: bool = False
    closed_evidence_text: str | None = None


class ExplicitClosureDetected(ValueError):
    pass


def tracked_content_hash(
    requirements: str,
    deadline_raw: str | None,
    recruitment_status: str | None,
) -> str:
    canonical = json.dumps(
        {
            "requirements": requirements,
            "deadline": deadline_raw,
            "recruitment_status": recruitment_status,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


class CollectionRequestError(RuntimeError):
    pass


class EvidenceHttpClient:
    SAFE_RESPONSE_HEADERS = {"content-type", "content-length", "date", "etag", "last-modified"}

    def __init__(self, *, timeout_seconds: int, max_retries: int, interval_ms: int) -> None:
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.interval_seconds = interval_ms / 1000
        self.request_count = 0
        self.retry_count = 0
        self._last_request_at = 0.0
        self._client = httpx.Client(timeout=timeout_seconds, follow_redirects=True)

    def close(self) -> None:
        self._client.close()

    def request(self, method: str, url: str, **kwargs: Any) -> CapturedResponse:
        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            wait = self.interval_seconds - (time.monotonic() - self._last_request_at)
            if wait > 0:
                time.sleep(wait)
            try:
                self.request_count += 1
                response = self._client.request(method, url, **kwargs)
                self._last_request_at = time.monotonic()
                if response.status_code == 429 or response.status_code >= 500:
                    raise CollectionRequestError(f"HTTP {response.status_code}")
                response.raise_for_status()
                headers = {
                    key.lower(): value
                    for key, value in response.headers.items()
                    if key.lower() in self.SAFE_RESPONSE_HEADERS
                }
                return CapturedResponse(
                    body=response.content,
                    request_url=str(response.url),
                    status_code=response.status_code,
                    content_type=response.headers.get("content-type"),
                    response_headers=headers,
                    retry_count=attempt,
                    captured_at=datetime.now(timezone.utc),
                )
            except (httpx.HTTPError, CollectionRequestError) as exc:
                last_error = exc
                if attempt >= self.max_retries:
                    break
                self.retry_count += 1
                time.sleep(min(2**attempt, 4))
        raise CollectionRequestError(f"请求失败（已重试 {self.max_retries} 次）：{last_error}")


def write_evidence(root: Path, relative_path: Path, body: bytes) -> Path:
    target = root / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + ".tmp")
    with temporary.open("wb") as stream:
        stream.write(body)
        stream.flush()
    temporary.replace(target)
    return target
