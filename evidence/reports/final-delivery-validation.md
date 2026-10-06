# 最终交付复核

复核日期：2026-10-06（Asia/Shanghai）

## 正式状态

- Docker：PostgreSQL、FastAPI、Nginx/React 三个正式服务均为 `healthy`，入口为 `http://localhost:8080`。
- 迁移：Alembic `20261006_0008 (head)`。
- 数据：3 个账号、37 个岗位、13 次运行、154 个 artifacts、135 个 observations、3 个 change sets、4 个 field changes、3 个筛选方案、4 个关注区间、9 条动态。
- 运行：7 次 live 全部成功；5 次 replay 成功；1 次明确标注的来源失败 replay；没有 pending/running 残留。
- 主要页面：`/`、`/login`、`/jobs`、`/watches`、`/watch-events`、`/maintenance/collection`、`/maintenance/replay` 均返回 200；两个 health endpoint 均返回 200/ok。

## JOB-01 至 JOB-09

| 场景 | 最终状态 | 复核依据 |
|---|---|---|
| JOB-01 | 通过 | 最终 live run：实习僧 10 个有效岗位，360 招聘 25 个；identity 和详情链接各自唯一。 |
| JOB-02 | 通过 | 360 最终刷新 25 条全部 unchanged；两个最终 run 均没有 change set 或 watch event；隔离测试验证完全相同内容不重复建档。 |
| JOB-03 | 通过 | 360 最终结果中 7 个同名“销售经理”对应 7 个不同 identity。 |
| JOB-04 | 通过 | 正式回放变化保留字段前后值，一次多字段变化合并一个 change set；三个有效关注窗口分别生成动态。 |
| JOB-05 | 通过 | 自动化测试确认关注前变化不补发，关注后变化可见。 |
| JOB-06 | 通过 | 正式库保留取消和再次关注区间；取消期间不新增动态，旧动态仍可追溯。 |
| JOB-07 | 通过 | 正式库保留 `REPLAY_SOURCE_FAILURE` 且 failed_count=0；失败不清空岗位，之后两个来源最终 live run 均成功。 |
| JOB-08 | 通过 | 三个账号的筛选、关注和动态按 user_id 隔离；跨用户操作拒绝，普通账号维护接口返回 403。 |
| JOB-09 | 通过 | 三个账号各保留一条同名“AI 北京岗位”方案；保存、修改、删除、重登持久化和基于当前岗位重新计算均由隔离测试通过。 |

逐项结果仍记录于 `evidence/templates/test-cases.csv`。

## 真实采集与 evidence

- 实习僧最终 run：`3b2699b4-e61e-4f24-b3d8-5b91e324d034`，60 个候选、10 个有效、2 个新增、8 个未变化、0 失败。
- 360 招聘最终 run：`8498d8d5-799c-478e-b88b-675bdeebd4a8`，25 个候选和有效岗位、25 个未变化、0 失败。
- 最终 run 共 39 个原始文件；逐文件大小和 SHA-256 均与数据库一致。
- 全部正式 artifacts 共 154 个、22,249,609 字节；逐文件复算结果为 0 缺失、0 大小不匹配、0 哈希不匹配。
- `evidence/raw/` 中仅两个 `.gitkeep` 不属于数据库 artifact，属于预期目录占位文件。
- 回放清单位于 `evidence/replay/scenarios/shixiseng-secretary/replay.json`，按原附件 JSON Schema 验证；回放快照引用真实原始 HTML，不冒充 live 数据。

## CSV 与校验清单

- `collection-runs.csv`：2 行，和两个最终 run 的正式统计一致。
- `source-evidence.csv`：2 行，声明的有效岗位数与 observation 的唯一 identity/URL 数一致。
- `test-cases.csv`：JOB-01 至 JOB-09 共 9 行。
- 三个 CSV 均为 UTF-8 BOM。
- `evidence/templates/SHA256SUMS` 原样保留。补回与原哈希完全一致的 `evidence/templates/README.md` 后，原附件清单仅有三个已填写 CSV 的预期差异。
- 根目录 `FINAL_SHA256SUMS` 独立覆盖最终提交文件；由 `scripts/generate-final-checksums.ps1` 重建并验证。

## 清理结果

- 删除 299 条仅用于反复登录验证的认证 session；容器重建后仍为 0。Session 不承载业务或 evidence 数据。
- 删除第十四步专用隔离卷 `job-tracker-step14_postgres_data`。
- 删除两个已停止且被正式 Compose 标记为 orphan 的旧测试容器。
- 三条筛选方案没有删除：保留原 ID、用户归属和 `AI + 北京` 条件，只将阶段性名称替换为“AI 北京岗位”，并同步历史 evidence 说明。
- 全部 live/replay 运行、原始 artifacts、回放、关注区间和动态均保留，因为它们被验收报告或业务追溯链引用。

## 最终测试

- 后端：隔离 PostgreSQL 与 evidence tmpfs，42 项通过，1 条第三方依赖弃用警告。
- 前端：5 个测试文件、8 项测试通过；生产构建成功。
- Docker：保留正式 PostgreSQL 卷执行 `docker compose up -d --build --force-recreate` 成功；迁移、初始化、业务数据和 evidence 索引保持一致。
- 已知非阻断提示：Ant Design v5/React 19 兼容提示、jsdom 伪元素提示、前端单 chunk 大于 500 KB。
