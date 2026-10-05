import hashlib
import json
from pathlib import Path

import pytest

from app.collectors.base import write_evidence
from app.collectors.careers_360 import parse_detail, parse_list


def test_parse_list_requires_successful_list_payload():
    payload = {"code": 0, "count": 2, "data": [{"id": "a"}, {"id": "b"}]}
    assert [item["id"] for item in parse_list(payload)] == ["a", "b"]
    with pytest.raises(ValueError):
        parse_list({"code": -1, "data": []})


def test_parse_detail_normalizes_fields_and_builds_stable_identity():
    payload = {
        "code": 0,
        "data": {
            "id": "stable-1",
            "title": " 安全工程师 ",
            "area": " 北京 ",
            "description": "岗位描述\r\n  负责安全建设  \n任职要求\n熟悉 Python",
            "qualification": "",
        },
    }
    job = parse_detail(payload)
    assert job.external_identity == "360-careers:stable-1"
    assert job.company == "360"
    assert job.title == "安全工程师"
    assert job.city == "北京"
    assert job.detail_url.endswith("/stable-1")
    assert job.requirements == "岗位描述\n负责安全建设\n任职要求\n熟悉 Python"
    assert len(job.content_hash) == 64

    canonical = json.dumps(
        {"requirements": job.requirements, "deadline": None, "recruitment_status": None},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    assert job.content_hash == hashlib.sha256(canonical).hexdigest()


def test_parse_detail_rejects_missing_required_fields():
    with pytest.raises(ValueError):
        parse_detail({"code": 0, "data": {"id": "x", "title": "岗位"}})


def test_same_title_with_different_360_ids_stays_distinct():
    base = {
        "title": "销售经理",
        "area": "北京",
        "description": "负责销售工作",
        "qualification": "",
    }
    first = parse_detail({"code": 0, "data": {**base, "id": "job-a"}})
    second = parse_detail({"code": 0, "data": {**base, "id": "job-b"}})
    assert first.title == second.title
    assert first.external_identity == "360-careers:job-a"
    assert second.external_identity == "360-careers:job-b"
    assert first.external_identity != second.external_identity
    assert first.detail_url != second.detail_url


def test_360_whitespace_normalization_produces_same_content_hash():
    first = parse_detail({
        "code": 0,
        "data": {"id": "same", "title": "岗位", "area": "北京", "description": "职责\r\n熟悉  Python", "qualification": ""},
    })
    second = parse_detail({
        "code": 0,
        "data": {"id": "same", "title": "岗位", "area": "北京", "description": "职责\n 熟悉 Python ", "qualification": ""},
    })
    assert first.requirements == second.requirements
    assert first.content_hash == second.content_hash


def test_evidence_writer_preserves_original_bytes(tmp_path):
    raw = b'{"text":"original\\r\\nbytes","value":1}'
    target = write_evidence(tmp_path, Path("raw/360/test.json"), raw)
    assert target.read_bytes() == raw
    assert not target.with_suffix(".json.tmp").exists()
