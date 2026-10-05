from datetime import timedelta

import pytest

from app.collectors.shixiseng import has_private_use_characters, parse_detail, parse_list


def test_parse_list_extracts_unique_stable_ids():
    html = b"""
    <a href="https://www.shixiseng.com/intern/inn_clean123?pcm=pc_SearchList">Clean job</a>
    <a href="/intern/inn_clean123">Duplicate</a>
    <a href="/intern/inn_second456">Second job</a>
    """
    assert parse_list(html) == [("inn_clean123", "Clean job"), ("inn_second456", "Second job")]


def test_parse_detail_extracts_fields_and_explicit_deadline():
    html = """
    <div class="new_job_name"><span>后端开发实习生</span></div>
    <div class="job_msg"><span class="job_position" title="北京">北京</span></div>
    <div class="job_detail">岗位职责：\n开发服务\n任职要求：\n熟悉 Python</div>
    <div class="con-job">投递要求：<div>截止日期：2026-12-31</div></div>
    <div class="job-about"><a class="com-name">示例公司</a></div>
    """.encode()
    job = parse_detail(html, "inn_clean123")
    assert job.external_identity == "shixiseng:inn_clean123"
    assert job.title == "后端开发实习生"
    assert job.company == "示例公司"
    assert job.city == "北京"
    assert job.deadline_raw == "2026-12-31"
    assert job.deadline_at is not None
    assert job.deadline_at.utcoffset() == timedelta(hours=8)
    assert job.recruitment_status is None


def test_private_use_font_characters_are_rejected():
    assert has_private_use_characters("岗位\ue000")
    html = """
    <div class="new_job_name">岗位\ue000</div>
    <span class="job_position" title="上海">上海</span>
    <div class="job_detail">岗位要求</div>
    <div class="job-about"><a class="com-name">公司</a></div>
    """.encode()
    with pytest.raises(ValueError, match="自定义字体"):
        parse_detail(html, "inn_private")
