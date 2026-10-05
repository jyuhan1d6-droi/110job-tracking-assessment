import re
from datetime import datetime
from typing import Any
from urllib.parse import urlunsplit
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup

from app.collectors.base import (
    CapturedResponse,
    EvidenceHttpClient,
    ExplicitClosureDetected,
    NormalizedJob,
    tracked_content_hash,
)

BASE_URL = "https://www.shixiseng.com"
LIST_URL = f"{BASE_URL}/interns/"
JOB_ID_PATTERN = re.compile(r"/intern/(inn_[A-Za-z0-9]+)")
DEADLINE_PATTERN = re.compile(r"截止日期[：:]\s*(\d{4}-\d{2}-\d{2})")
CLOSED_PATTERN = re.compile(r"(?:该)?职位(?:已下架|已结束|已关闭|已停止招聘)|停止招聘")


def has_private_use_characters(value: str) -> bool:
    return any(0xE000 <= ord(character) <= 0xF8FF for character in value)


def clean_text(value: Any) -> str:
    text = str(value or "").replace("\r\n", "\n").replace("\r", "\n")
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.split("\n")]
    return "\n".join(line for line in lines if line).strip()


def parse_list(html: bytes) -> list[tuple[str, str]]:
    soup = BeautifulSoup(html, "html.parser")
    jobs: list[tuple[str, str]] = []
    seen: set[str] = set()
    for anchor in soup.select("a[href]"):
        href = anchor.get("href") or ""
        match = JOB_ID_PATTERN.search(href)
        if not match or match.group(1) in seen:
            continue
        title = clean_text(anchor.get_text(" ", strip=True))
        if not title:
            continue
        seen.add(match.group(1))
        jobs.append((match.group(1), title))
    if not jobs:
        raise ValueError("实习僧列表没有解析到岗位链接")
    return jobs


def parse_detail(html: bytes, expected_job_id: str) -> NormalizedJob:
    soup = BeautifulSoup(html, "html.parser")
    page_text = clean_text(soup.get_text(" ", strip=True))
    closed_match = CLOSED_PATTERN.search(page_text)
    if closed_match:
        raise ExplicitClosureDetected(closed_match.group(0))
    title_node = soup.select_one(".new_job_name")
    city_node = soup.select_one(".job_position")
    requirements_node = soup.select_one(".job_detail")
    company_node = soup.select_one(".job-about .com-name")
    if not all((title_node, city_node, requirements_node, company_node)):
        raise ValueError("实习僧详情页结构缺少岗位名称、公司、城市或岗位要求")
    title = clean_text(title_node.get_text(" ", strip=True))
    city = clean_text(city_node.get("title") or city_node.get_text(" ", strip=True))
    requirements = clean_text(requirements_node.get_text("\n", strip=True))
    company = clean_text(company_node.get_text(" ", strip=True))
    required = (title, company, city, requirements)
    if any(not value for value in required):
        raise ValueError("实习僧详情必需字段为空")
    if any(has_private_use_characters(value) for value in required):
        raise ValueError("实习僧详情包含需自定义字体还原的字符，已跳过")

    deadline_raw = None
    deadline_at = None
    for node in soup.select(".con-job"):
        match = DEADLINE_PATTERN.search(clean_text(node.get_text(" ", strip=True)))
        if match:
            deadline_raw = match.group(1)
            deadline_at = datetime.strptime(deadline_raw, "%Y-%m-%d").replace(
                hour=23, minute=59, second=59, tzinfo=ZoneInfo("Asia/Shanghai")
            )
            break

    detail_url = urlunsplit(("https", "www.shixiseng.com", f"/intern/{expected_job_id}", "", ""))
    return NormalizedJob(
        external_identity=f"shixiseng:{expected_job_id}",
        title=title,
        company=company,
        city=city,
        requirements=requirements,
        deadline_raw=deadline_raw,
        deadline_at=deadline_at,
        recruitment_status=None,
        detail_url=detail_url,
        content_hash=tracked_content_hash(requirements, deadline_raw, None),
    )


class ShixisengCollector:
    headers = {
        "Accept": "text/html,application/xhtml+xml",
        "Referer": LIST_URL,
        "User-Agent": "JobTrackerAssessment/1.0 (+https://www.shixiseng.com/interns/)",
    }

    def __init__(self, client: EvidenceHttpClient) -> None:
        self.client = client

    def fetch_list(self, page: int) -> CapturedResponse:
        return self.client.request("GET", LIST_URL, params={"page": page}, headers=self.headers)

    def fetch_detail(self, job_id: str) -> CapturedResponse:
        return self.client.request("GET", f"{BASE_URL}/intern/{job_id}", headers=self.headers)
