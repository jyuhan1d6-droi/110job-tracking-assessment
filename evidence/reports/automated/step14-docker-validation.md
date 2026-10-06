# 第十四步：Docker 全链路与持久化验证

验证日期：2026-10-06（Asia/Shanghai）

## 隔离边界

- Compose 项目：`job-tracker-step14`
- 入口：`http://localhost:18080`
- PostgreSQL 卷：`job-tracker-step14_postgres_data`
- 未调用真实采集接口，未生成或修改正式采集 evidence。
- 正式应用 `http://localhost:8080` 及其 PostgreSQL 卷未参与从零和持久化测试。

## 从零构建

先清理上述隔离项目及其专用卷，再执行 `docker compose -p job-tracker-step14 up -d --build`。结果：

- PostgreSQL、FastAPI、Nginx/React 三个服务均为 `healthy`。
- Alembic 从空数据库依次执行 `20261005_0001` 到 `20261006_0008 (head)`。
- 初始化结果为 3 个账号、2 个来源、0 个岗位、0 个筛选方案、0 个关注、0 个动态、0 个回放运行。
- `/api/health` 与 `/api/health/database` 均返回 200/ok。
- `/`、`/login`、`/jobs`、`/watches`、`/watch-events`、`/maintenance/collection`、`/maintenance/replay` 均由 Nginx 正常返回前端入口。
- 未登录访问岗位 API 返回 401；普通账号访问采集与回放 API 返回 403；维护账号访问两类维护 API 返回 200。
- 空数据时岗位摘要为 `total_visible_jobs=0`，与首次采集引导条件一致。

## 保留数据卷重建与重启

仅在隔离库插入一组带 `step14_fixture` 元数据的非采集验证夹具，包含：岗位、筛选方案、关注区间、关注动态、成功完成的 live 运行和成功完成的 replay 运行。重建前结果：3 个账号、1 个岗位、1 个筛选方案、1 个关注、1 个动态、1 个已完成回放；业务记录 ID 指纹为 `172976d03185292e3c8a8d18a35eaff6`。

执行 `docker compose -p job-tracker-step14 up -d --build --force-recreate` 后：

- 同一 PostgreSQL 卷被保留。
- 上述计数和 ID 指纹完全一致。
- 三个预置账号均可重新登录。
- `jobseeker1` 通过 API 可读取 1 个岗位、1 个筛选方案、1 个关注和 1 个动态。

随后重启整套 Compose 服务，三个服务重新达到 `healthy`；上述数据和已完成回放记录仍存在。

## 中断恢复规则

在隔离库建立明确标注的状态夹具后重启后端：

- `live/pending` 转为 `failed`，`error_code=PROCESS_INTERRUPTED`，写入 `finished_at`。
- `live/running` 转为 `failed`，`error_code=PROCESS_INTERRUPTED`，写入 `finished_at`。
- 同时存在的 `replay/running` 经两次后端重启和一次整套服务重启后仍为 `running`，没有 `error_code` 和 `finished_at`。
- 先于应用健康状态查询会短暂读到旧的 pending 状态；等待 health check 通过后恢复结果正确。验证脚本据此改为先等待健康，不需要修改业务代码。

## 正式应用页面检查

使用三个预置账号实际登录 `http://localhost:8080`：

- `jobseeker1`：岗位页显示 35 个真实岗位、自己的筛选方案；关注动态页显示 3 条动态。
- `jobseeker2`：岗位、我的关注、关注动态均可正常加载；只显示自己的 1 个当前关注和 3 条动态。
- `maintainer`：数据采集页显示两个固定来源、最近状态、运行统计和历史；本地回放页明确标注回放，并展示原始证据、快照与声明字段。未点击真实采集或执行回放。
- 岗位页输入无匹配关键词后显示“未找到符合条件的岗位，请调整关键词或城市”；隔离空库的岗位摘要为 0，用于触发首次采集引导。

## 正式数据库残余检查

只读盘点正式库的 35 个岗位、11 次采集/回放运行、115 个 artifact、筛选、关注和动态，并搜索 test/demo/temp/fixture/测试/验证/临时等标记。

删除：

- 1 条 `jobseeker1` 对“销售经理”的已取消关注记录。该区间只持续约 1 秒、没有任何动态、未被文档或 evidence 引用，可明确确认是页面开发验证残余。

保留：

- 35 个岗位、全部 live/replay 运行及 115 个 artifacts：均来自真实采集、重复采集或正式回放链路。
- 3 条当时名为“第九步持久化验证”的筛选方案：被 `evidence/reports/saved-filter-validation.md` 明确引用，用于三个账号持久化与隔离验收；最终收口时保留原记录和条件并改名为“AI 北京岗位”。
- “秘书”岗位的 4 个关注区间与 9 条动态：承载取消再关注、三个账号隔离和回放变化的正式验收结果。

清理后正式库为 4 个关注区间、9 条动态；未删除任何真实岗位、运行、artifact、回放或 evidence 引用的数据。
