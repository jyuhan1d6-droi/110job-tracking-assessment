# 岗位搜索与变更追踪

面向求职者的岗位搜索、条件收藏、岗位关注与变化追踪应用。当前已完成 Docker 基础工程、核心采集数据模型和服务端 Session 登录；真实采集、筛选、关注与回放将在后续阶段实现。

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
- 尚未实现筛选方案、关注、动态或回放服务逻辑。

## 岗位浏览

登录后访问 <http://localhost:8080/jobs>。关键词匹配岗位名称或岗位要求，城市按来源原值精确匹配；两项同时设置时必须同时满足。岗位详情保留来源明确提供的截止时间和招聘状态，缺失字段显示“未提供”。
- 尚未加入 Playwright；将在核心业务完成后再添加端到端测试。

详细目录和证据要求见 `docs/architecture.md`、`docs/sources.md` 与 `evidence/README.md`。
