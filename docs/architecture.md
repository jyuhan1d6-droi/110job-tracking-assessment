# 架构说明

浏览器只访问 Nginx。Nginx 提供 Vite 构建产物，并将 `/api` 请求反向代理到 FastAPI。FastAPI 通过 SQLAlchemy 访问 PostgreSQL。数据库使用命名卷持久化；项目根目录的 `evidence/` 绑定挂载到容器 `/evidence`，原始 HTML、JSON 和测试证据可直接检查并随仓库提交。

后续业务实现遵循以下边界：

- 每个采集来源是独立 adapter，一个来源失败不影响另一个来源。
- 原始响应先保存，再解析入库。
- 岗位由 `(source_id, external_identity)` 唯一标识。
- 列表缺失、请求失败和解析失败均不自动关闭岗位。
- 只有来源明确给出关闭证据时才记录关闭。
- 用户资源必须在后端按当前用户 ID 隔离。
- 回放复用与真实采集相同的比较逻辑，不直接写入预期结果。
