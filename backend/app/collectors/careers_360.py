import hashlib
import json
import re
from typing import Any

from app.collectors.base import CapturedResponse, EvidenceHttpClient, NormalizedJob

BASE_URL = "https://hr.360.cn"
LIST_URL = f"{BASE_URL}/v2/index/getlistsearch"
DETAIL_URL = f"{BASE_URL}/v2/index/getjobone"


def _clean_text(value: Any) -> str:
    text = str(value or "").replace("\r\n", "\n").replace("\r", "\n")
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.split("\n")]
    return "\n".join(line for line in lines if line).strip()


def parse_list(payload: dict[str, Any]) -> list[dict[str, Any]]:
    if payload.get("code") != 0 or not isinstance(payload.get("data"), list):
        raise ValueError(f"360 列表响应异常：code={payload.get('code')!r}")
    return payload["data"]


def parse_detail(payload: dict[str, Any]) -> NormalizedJob:
    if payload.get("code") != 0 or not isinstance(payload.get("data"), dict):
        raise ValueError(f"360 详情响应异常：code={payload.get('code')!r}")
    data = payload["data"]
    job_id = _clean_text(data.get("id"))
    title = _clean_text(data.get("title"))
    city = _clean_text(data.get("area"))
    description = _clean_text(data.get("description"))
    qualification = _clean_text(data.get("qualification"))
    if not job_id or not title or not city or not (description or qualification):
        raise ValueError("360 详情缺少岗位 ID、名称、城市或岗位要求")
    parts = []
    if description:
        parts.append(description)
    if qualification and qualification not in description:
        parts.append(f"任职要求\n{qualification}")
    requirements = "\n\n".join(parts)
    identity = f"360-careers:{job_id}"
    detail_url = f"{BASE_URL}/hr/detail/{job_id}"
    canonical = json.dumps(
        {
            "requirements": requirements,
            "deadline": None,
            "recruitment_status": None,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return NormalizedJob(
        external_identity=identity,
        title=title,
        company="360",
        city=city,
        requirements=requirements,
        detail_url=detail_url,
        content_hash=hashlib.sha256(canonical).hexdigest(),
    )


class Careers360Collector:
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://hr.360.cn/hr/list",
        "Origin": "https://hr.360.cn",
        "User-Agent": "JobTrackerAssessment/1.0 (+https://hr.360.cn/hr/list)",
    }

    def __init__(self, client: EvidenceHttpClient) -> None:
        self.client = client

    def fetch_list(self) -> CapturedResponse:
        return self.client.request("POST", LIST_URL, json={"limit": 10000, "page": 1}, headers=self.headers)

    def fetch_detail(self, job_id: str) -> CapturedResponse:
        return self.client.request("GET", DETAIL_URL, params={"id": job_id}, headers=self.headers)
