# 岗位搜索与变更追踪

面向求职者的岗位搜索、条件收藏、岗位关注与变化追踪应用。

## 已确定的数据来源

- 招聘平台：实习僧（`recruitment_platform`）
- 公司官方招聘网站：360 招聘（`company_careers`）

采集器固定为以上两个来源，不会在错误时静默切换站点。

## 技术栈

- 前端：React、TypeScript、Vite、React Router、TanStack Query、Ant Design
- 后端：Python、FastAPI、SQLAlchemy、Alembic、HTTPX、Beautiful Soup
- 数据库：PostgreSQL 17
- 部署：Docker Compose；Nginx 提供前端并将 `/api` 代理到 FastAPI

## 架构

```text
浏览器
  └─ Nginx：同源提供 React 静态资源并代理 /api
       └─ FastAPI：认证、权限、搜索、采集、比较、关注与回放
            ├─ PostgreSQL：业务数据、Session、运行与证据索引
            └─ /evidence：宿主机绑定目录，保存原始 HTML/JSON 和验收材料
```

`frontend/Dockerfile` 构建前端并生成 Nginx 镜像，`backend/Dockerfile` 构建后端；根目录 `compose.yaml` 组合前端、后端和 PostgreSQL。数据库使用命名卷持久化，evidence 使用项目目录绑定挂载。容器启动时后端自动执行 Alembic 迁移和幂等账号/来源初始化。

## 启动

1. 复制环境变量：

   ```bash
   cp .env.example .env
   ```

   Windows PowerShell：

   ```powershell
   Copy-Item .env.example .env
   ```

2. 修改 `.env` 中的数据库密码、三个预置账号密码，以及 HTTPS 环境下的 Cookie 配置。

3. 构建并启动：

   ```bash
   docker compose up --build
   ```

   如果 Docker 使用独立 Compose 命令：

   ```bash
   docker-compose up --build
   ```

   首次启动会等待 PostgreSQL 健康、自动执行全部 Alembic 迁移，再幂等初始化三个账号和两个固定来源。无需在宿主机安装 Node.js、Python 或 PostgreSQL。

4. 打开 <http://localhost:8080>。

5. 健康检查：

   ```bash
   curl http://localhost:8080/api/health
   curl http://localhost:8080/api/health/database
   ```

## 预置账号与登录

首次启动时会幂等创建以下账号，密码由 `.env` 中对应的 `SEED_*_PASSWORD` 配置：

- `jobseeker1` / 示例密码 `exam-jobseeker1`：普通求职者
- `jobseeker2` / 示例密码 `exam-jobseeker2`：普通求职者，用于验证用户数据隔离
- `maintainer` / 示例密码 `exam-maintainer`：数据维护账号

以上密码是 `.env.example` 的本地验收默认值，部署前应在 `.env` 中修改；真实密码不会写入前端代码。

应用通过 Nginx 同源访问后端，认证使用数据库中的服务端 Session 和 HttpOnly Cookie。HTTP 验收环境使用 `SESSION_COOKIE_SECURE=false`；部署到 HTTPS 后必须设为 `true`。重新运行初始化不会覆盖已有账号密码。

停止容器但保留 PostgreSQL 数据卷：

```bash
docker compose down
```

重建容器并验证数据卷：

```bash
docker compose up -d --build --force-recreate
docker compose ps
```

三个服务均显示 `healthy` 后再访问应用。不要使用 `docker compose down -v`，该命令会删除数据库卷。采集证据直接保存在项目根目录的 `evidence/`，便于检查和提交。

## 实际操作顺序

1. 使用 `maintainer` 登录，进入“数据采集”，分别选择 360 招聘和实习僧。点击“开始真实采集”后，在运行历史查看新增、变化、未变化、失败数量与失败原因；“详情与证据”用于核对每个原始响应的路径、大小、HTTP 状态和 SHA-256。
2. 使用普通账号登录“岗位”，按关键词和城市搜索。两项同时填写时执行 AND 查询；首次还没有岗位时，页面会提示联系维护账号先采集。
3. 在岗位页保存当前条件。筛选方案可使用、编辑和删除；再次使用时会查询当前数据库，不复用旧结果。
4. 在岗位列表或详情关注岗位；“我的关注”仅显示当前账号仍在关注的岗位。
5. 维护账号可在“本地回放”执行明确标注的回放场景。回放不会访问外部招聘网站，也不会作为新的真实采集结果。
6. 普通账号进入“关注动态”查看关注期间产生的变化，再进入变化详情核对字段修改前后内容；关注前或取消关注期间的变化不会补发。

本步骤已在独立 Compose 项目中验证全新空卷启动、迁移初始化、保留数据卷重建和整套服务重启。验证记录见 `evidence/reports/automated/step14-docker-validation.md`。

## 当前状态

- 已建立前端、后端、数据库和反向代理骨架。
- 已提供后端应用及数据库健康检查。
- 已建立 Alembic，容器启动时自动执行迁移；当前主模型包含用户、来源、采集运行、证据索引、岗位、岗位观察和两级变更记录。
- 已建立完整的证据目录约定并纳入附件模板。
- 已实现三个预置账号、Argon2id 密码、服务端 Session 登录/退出、登录状态恢复和维护员角色限制。
- 已完成 360 招聘公开 JSON 接口的真实采集、原始响应证据、运行统计和首次入库；首次正式运行获取 25 个有效岗位。
- 已完成实习僧公开 HTML 列表与详情的真实采集、原始响应证据、运行统计和首次入库；首次正式运行获取 10 个有效岗位。
- 已完成重复刷新去重、岗位要求/截止时间/招聘状态字段比较，以及带来源证据的明确关闭规则。
- 已完成岗位列表、详情、关键词/城市 AND 搜索、分页以及首次无数据引导；筛选条件保存在页面 URL。
- 已完成用户筛选方案的保存、修改、删除和复用；方案使用时基于当前岗位数据重新查询，三个账号的数据由后端隔离。
- 已完成岗位关注、取消关注、当前关注列表和可重复关注的时间区间；岗位列表及详情按当前账号显示关注状态。
- 已完成关注动态生成、动态列表和字段变更详情；只对关注区间内新发生的变化建立动态，不补发历史变化。
- 已完成基于真实采集证据的本地回放入口，清单按附件 `replay.schema.json` 校验，支持字段变化、重复回放、明确关闭和来源级失败。
- 最终真实采集：实习僧有效 10 条、360 招聘有效 25 条；39 个最终原始文件的大小与 SHA-256 已逐项复核。

## 岗位浏览

登录后访问 <http://localhost:8080/jobs>。关键词匹配岗位名称或岗位要求，城市按来源原值精确匹配；两项同时设置时必须同时满足。岗位详情保留来源明确提供的截止时间和招聘状态，缺失字段显示“未提供”。

数据维护账号可访问 <http://localhost:8080/maintenance/collection>，选择实习僧或 360 招聘执行真实采集。页面会显示当前状态、运行统计、失败原因、历史记录及原始证据元数据，并可按证据 ID 安全下载文件。采集超时、重试次数和请求间隔来自数据库 `sources` 配置；`.env.example` 不再提供无效的同名环境变量。

## 隔离自动化测试

后端验收测试必须使用独立的临时 PostgreSQL 和 evidence tmpfs，禁止直接对正式数据库执行 `pytest`：

```bash
docker compose -f compose.test.yaml up --build --abort-on-container-exit --exit-code-from backend-test
```

测试容器要求 `APP_ENV=test`、数据库名以 `_test` 结尾，并将项目 `evidence/` 只读挂载为真实证据来源；测试产生的文件仅写入 `/test-evidence`。JOB-01 至 JOB-09 的结果见 `evidence/templates/test-cases.csv` 和 `evidence/reports/automated/step13-acceptance-validation.md`。

## 筛选方案

在岗位页执行搜索后，点击“保存当前条件”，输入名称即可收藏当前关键词和城市。方案支持使用、编辑和删除；点击“使用”会用数据库中的最新岗位重新计算结果，不保存或复用旧的岗位列表。方案属于当前账号，其他普通账号和维护账号均不能读取或修改。

## 岗位关注

岗位卡片和详情页均可关注或取消关注。导航中的“我的关注”只展示当前账号仍在关注的岗位。取消关注会结束当前关注区间而不是删除历史；再次关注将建立新区间，供后续按时间边界生成关注动态。时间区间采用 `[watched_at, unwatched_at)`：关注时刻包含，取消时刻不包含。

导航中的“关注动态”展示关注期间新发生的岗位要求、截止时间或招聘状态变化。一次采集中的多个字段变化合并为一条动态，详情页逐项保留修改前后原文。关注前及取消期间的变化不会补发。系统不提供用户物理删除功能。

## 本地回放

维护账号可访问 <http://localhost:8080/maintenance/replay>。页面中的所有场景均明确标注“本地回放”，不会访问招聘网站，也不能作为新的真实采集结果。回放清单兼容题目附件的 `evidence/templates/replay.schema.json`；`changes` 仅供复核，应用只根据解析后的快照与当前岗位值比较生成变化。来源级失败没有具体岗位失败，因此 `failed_count` 保持 0。

## 关键取舍

- 使用服务端 Session 和 HttpOnly Cookie，避免为同源验收应用引入 access/refresh token 轮换复杂度；HTTPS 环境通过 `SESSION_COOKIE_SECURE=true` 启用 Secure。
- 岗位身份只使用“来源 + 稳定岗位 ID”，不按标题合并；同名不同 ID 始终保持独立。
- 原始响应必须先落盘并建立 artifact 记录，之后才解析入库；证据写入失败时不产生无法追溯的岗位更新。
- 网络请求不持有数据库长事务；两个来源独立运行，单来源失败不清空历史数据，也不影响另一来源。
- 只比较岗位要求、截止时间、招聘状态三个跟踪字段。首次采集不产生变化；无实际变化不创建 change set 或关注动态。
- 列表缺失、超时、403、429、5xx 和解析失败都不能推断岗位关闭；只有来源明确给出关闭证据才记录 closed。
- 关注采用 `[watched_at, unwatched_at)` 时间区间；取消关注不删除历史，重新关注建立新区间。
- 回放复用真实解析和比较链路，但使用 `mode=replay` 明确隔离，不更新最近真实采集时间，也不冒充 live 数据。

## 已知限制

- 仅支持手动采集，不包含定时任务、跨来源岗位合并、自动推送、智能推荐或投递管理。
- 外部站点页面或公开接口结构变化会导致相应来源失败；失败会保留已有岗位并在运行详情展示原因。
- 实习僧采集器为控制频率，每次从当前公开列表候选中选取 10 个可完整解析且不含私用区字体字符的岗位；数据库可保留历次出现过的更多岗位。
- 不根据截止时间自动关闭岗位，来源未公开的字段显示“未提供”。
- 筛选方案名称按 PostgreSQL 精确字符串比较，大小写不同可同时存在；城市按来源原值精确匹配，“北京”和“北京市”视为不同值。
- 前端生产构建存在单个 JavaScript chunk 大于 500 KB 的性能提醒，不影响题目功能；本项目未为少量关键页面额外引入 Playwright 基础设施，页面逻辑由 Vitest/API mock、隔离数据库测试和实际 Docker 页面检查共同覆盖。

## 交付清单

- 前后端源码：`frontend/`、`backend/`
- Docker 部署：`frontend/Dockerfile`、`backend/Dockerfile`、`compose.yaml`、`.env.example`
- 数据库迁移与初始化：`backend/alembic/`、容器启动脚本及三个预置账号
- 来源与架构说明：`docs/sources.md`、`docs/architecture.md`
- 两次最终真实采集：`evidence/templates/collection-runs.csv`
- 两类来源证据：`evidence/templates/source-evidence.csv`
- JOB-01 至 JOB-09：`evidence/templates/test-cases.csv`
- 最终原始证据明细：`evidence/reports/final-live-artifacts.csv`
- 最终采集、自动化、Docker、回放和功能报告：`evidence/reports/`
- 真实原始 HTML/JSON：`evidence/raw/`
- 回放清单与快照：`evidence/replay/`
- 原附件校验：`evidence/templates/SHA256SUMS`
- 最终提交材料校验：`FINAL_SHA256SUMS`

详细目录和证据要求见 `docs/architecture.md`、`docs/sources.md` 与 `evidence/README.md`。
