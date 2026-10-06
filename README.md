# 岗位搜索与变更追踪

面向求职者的岗位搜索、条件收藏、岗位关注与变化追踪应用。

## 已确定的数据来源

- 招聘平台：实习僧（`recruitment_platform`）
- 公司官方招聘网站：360 招聘（`company_careers`）
- 腾讯招聘仅作为故障备选，未经确认不切换来源。

## 技术栈

- 前端：React、TypeScript、Vite、React Router、TanStack Query、Ant Design
- 后端：Python、FastAPI、SQLAlchemy、Alembic、HTTPX、Beautiful Soup
- 数据库：PostgreSQL 17
- 部署：Docker Compose；Nginx 提供前端并将 `/api` 代理到 FastAPI

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

4. 打开 <http://localhost:8080>。

5. 健康检查：

   ```bash
   curl http://localhost:8080/api/health
   curl http://localhost:8080/api/health/database
   ```

## 预置账号与登录

首次启动时会幂等创建以下账号，密码由 `.env` 中对应的 `SEED_*_PASSWORD` 配置：

- `jobseeker1`：普通求职者
- `jobseeker2`：普通求职者，用于验证用户数据隔离
- `maintainer`：数据维护账号

应用通过 Nginx 同源访问后端，认证使用数据库中的服务端 Session 和 HttpOnly Cookie。HTTP 验收环境使用 `SESSION_COOKIE_SECURE=false`；部署到 HTTPS 后必须设为 `true`。重新运行初始化不会覆盖已有账号密码。

停止容器但保留数据：

```bash
docker-compose down
```

重建容器并验证数据卷：

```bash
docker-compose up --build --force-recreate
```

不要使用 `docker-compose down -v`，该命令会删除数据库卷。采集证据直接保存在项目根目录的 `evidence/`，便于检查和提交。

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

## 岗位浏览

登录后访问 <http://localhost:8080/jobs>。关键词匹配岗位名称或岗位要求，城市按来源原值精确匹配；两项同时设置时必须同时满足。岗位详情保留来源明确提供的截止时间和招聘状态，缺失字段显示“未提供”。

## 筛选方案

在岗位页执行搜索后，点击“保存当前条件”，输入名称即可收藏当前关键词和城市。方案支持使用、编辑和删除；点击“使用”会用数据库中的最新岗位重新计算结果，不保存或复用旧的岗位列表。方案属于当前账号，其他普通账号和维护账号均不能读取或修改。

## 岗位关注

岗位卡片和详情页均可关注或取消关注。导航中的“我的关注”只展示当前账号仍在关注的岗位。取消关注会结束当前关注区间而不是删除历史；再次关注将建立新区间，供后续按时间边界生成关注动态。时间区间采用 `[watched_at, unwatched_at)`：关注时刻包含，取消时刻不包含。

导航中的“关注动态”展示关注期间新发生的岗位要求、截止时间或招聘状态变化。一次采集中的多个字段变化合并为一条动态，详情页逐项保留修改前后原文。关注前及取消期间的变化不会补发。系统不提供用户物理删除功能。

## 本地回放

维护账号可访问 <http://localhost:8080/maintenance/replay>。页面中的所有场景均明确标注“本地回放”，不会访问招聘网站，也不能作为新的真实采集结果。回放清单兼容题目附件的 `evidence/templates/replay.schema.json`；`changes` 仅供复核，应用只根据解析后的快照与当前岗位值比较生成变化。来源级失败没有具体岗位失败，因此 `failed_count` 保持 0。
- 尚未加入 Playwright；将在核心业务完成后再添加端到端测试。

详细目录和证据要求见 `docs/architecture.md`、`docs/sources.md` 与 `evidence/README.md`。
