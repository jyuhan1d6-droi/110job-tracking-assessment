# 验收证据目录

本目录保存可提交、可复核的完整采集和测试证据。现已包含实习僧和 360 招聘的真实原始响应、运行报告，以及明确标注的本地回放材料。

## 目录约定

- `raw/shixiseng/<run_id>/`：`list-page-*.html` 与 `detail-<identity>.html`，均为未经改写的原始响应字节。
- `raw/360-careers/<run_id>/`：`list-page-*.json` 与 `detail-<identity>.json`，均为未经改写的原始响应字节。
- 每个原始文件的请求 URL、最终 URL、HTTP 状态、响应头、抓取时间、大小和 SHA-256 保存在数据库 `collection_artifacts`；维护页可按运行查询并安全下载。最终两次 live run 的逐文件导出见 `reports/final-live-artifacts.csv`。
- `replay/scenarios/`：兼容附件 `replay.schema.json` 的清单，以及明确标注为回放的派生快照。
- `replay/runs/`：每次回放实际保存的清单与快照副本；不作为新的真实采集证据。
- `reports/`：真实采集、回放、Docker、功能和自动化测试报告。
- `templates/`：题目附件及正式填写的三个验收 CSV。`templates/SHA256SUMS` 保留为原附件校验，不因填写 CSV 而覆盖。
- 整个 `evidence/` 绑定挂载到后端容器的 `/evidence`；真实材料按上述目录直接落在宿主机并可纳入 Git。

任何原始 HTML/JSON 均按响应原始字节保存，不重编码、不改写。仓库根目录 `FINAL_SHA256SUMS` 是最终提交材料的独立校验清单，不替代原附件的 `templates/SHA256SUMS`。
