import re
from typing import Any

from app.collectors.base import (
    CapturedResponse,
    EvidenceHttpClient,
    ExplicitClosureDetected,
    NormalizedJob,
    tracked_content_hash,
)

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
        message = _clean_text(payload.get("msg"))
        if any(phrase in message for phrase in ("已下架", "已结束", "停止招聘", "已关闭")):
            raise ExplicitClosureDetected(message)
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
    raw_status = _clean_text(data.get("status") or data.get("job_status") or data.get("state"))
    closed_values = {"closed", "offline", "已下架", "已结束", "停止招聘", "已关闭"}
    open_values = {"open", "招聘中", "在招"}
    status_key = raw_status.lower()
    recruitment_status = "closed" if status_key in closed_values else "open" if status_key in open_values else None
    explicit_closed = recruitment_status == "closed"
    closed_evidence = f"360 明确状态字段：{raw_status}" if explicit_closed else None
    identity = f"360-careers:{job_id}"
    detail_url = f"{BASE_URL}/hr/detail/{job_id}"
    return NormalizedJob(
        external_identity=identity,
        title=title,
        company="360",
        city=city,
        requirements=requirements,
        detail_url=detail_url,
        recruitment_status=recruitment_status,
        explicit_closed=explicit_closed,
        closed_evidence_text=closed_evidence,
        content_hash=tracked_content_hash(requirements, None, recruitment_status),
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
