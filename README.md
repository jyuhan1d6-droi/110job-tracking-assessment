# 岗位搜索与变更追踪

面向求职者的岗位搜索、条件收藏、岗位关注与变化追踪应用。本仓库当前完成基础工程和 Docker 部署骨架；真实采集、账号业务、筛选、关注与回放将在后续阶段实现。

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

2. 修改 `.env` 中的数据库密码和 `APP_SECRET_KEY`。

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
- 尚未实现真实采集、认证、筛选方案、关注、动态或回放服务逻辑。
- 尚未加入 Playwright；将在核心业务完成后再添加端到端测试。

详细目录和证据要求见 `docs/architecture.md`、`docs/sources.md` 与 `evidence/README.md`。
