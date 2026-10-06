# 第十三步：隔离自动化验收

执行时间：2026-10-06（Asia/Shanghai）

## 隔离环境

- Compose：`compose.test.yaml`。
- 数据库：独立服务 `postgres-test`，数据库名 `job_tracker_test`，数据目录使用 tmpfs。
- evidence：正式目录只读挂载为 `/source-evidence`；测试写入 `/test-evidence` tmpfs。
- 安全门：pytest 要求 `APP_ENV=test`、数据库名以 `_test` 结尾且两个 evidence 根目录不同，否则拒绝运行。
- 每个测试前后清空隔离库业务表并重建最小基线岗位；不依赖正式数据库岗位。
- 正式数据库复核计数：users=3、sources=2、runs=11、jobs=35、filters=3、watches=4、events=9；隔离测试执行后保持不变。

## 执行结果

- 后端：42 passed；JUnit XML：`evidence/reports/automated/job-tracker-junit.xml`。
- 前端：8 passed。
- 前端生产构建：成功。
- Playwright：本步未引入。关键采集页面用隔离的 Vitest/API mock 验证；跨用户、筛选刷新、关注窗口和来源失败由独立 PostgreSQL 的真实 API/服务链路验证，避免为少量流程扩展浏览器基础设施。

## JOB-01 至 JOB-09

| 场景 | 结果 | 自动化证据 |
| --- | --- | --- |
| JOB-01 | 通过。解析提交的 360 与实习僧真实原始证据，各不少于 10 条，identity 唯一且详情链接可追溯。 | `backend/tests/test_acceptance_scenarios.py::test_job_01_committed_real_evidence_has_two_sources_and_at_least_ten_valid_jobs_each` |
| JOB-02 | 通过。相同内容重复入库为 unchanged，不创建 change set。 | `backend/tests/test_acceptance_scenarios.py::test_job_02_and_03_repeat_is_unchanged_while_same_title_different_identity_stays_distinct` |
| JOB-03 | 通过。同名不同 identity 建立两条岗位。 | 同 JOB-02 测试 |
| JOB-04 | 通过。关注后一次多字段变化建立一个 change set、多条 field change，每个有效关注窗口一条动态。 | `backend/tests/test_change_tracking.py::test_job_04_05_06_watch_change_boundaries_cancel_and_refollow_are_persisted` |
| JOB-05 | 通过。关注前变化不补发，关注后变化进入动态。 | 同 JOB-04 测试 |
| JOB-06 | 通过。取消期间不新增动态，旧动态保留；重新关注建立新窗口。 | 同 JOB-04 测试及 `test_watch_time_boundary_is_left_closed_right_open` |
| JOB-07 | 通过。测试环境替换 360 HTTP 层为受控超时；来源级 failed_count=0、原岗位保留，实习僧来源仍独立成功。生产接口未增加测试后门。 | `backend/tests/test_acceptance_scenarios.py::test_job_07_source_failure_preserves_jobs_and_does_not_block_other_source` |
| JOB-08 | 通过。三个账号的筛选、关注和动态由后端按 user_id 隔离；跨用户 UUID 操作返回 404，普通用户采集/回放接口返回 403。 | `backend/tests/test_saved_filters.py`、`backend/tests/test_watches.py`、`backend/tests/test_collection_admin.py` |
| JOB-09 | 通过。保存方案后替换当前岗位集合，再使用相同关键词和城市得到重新计算结果；重新登录后方案仍存在。 | `backend/tests/test_acceptance_scenarios.py::test_job_09_saved_filter_reuse_recomputes_against_refreshed_jobs_and_survives_login` |

## 交付边界

- 本步填写 `test-cases.csv`。
- `collection-runs.csv` 和 `source-evidence.csv` 留待第十五步结合最终真实采集统一定稿。
