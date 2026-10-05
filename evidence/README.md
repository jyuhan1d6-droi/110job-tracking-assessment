# 验收证据目录

本目录保存可提交、可复核的完整采集和测试证据。真实采集尚未开始，当前只有目录约定与题目附件模板。

## 目录约定

- `raw/shixiseng/<run_id>/`
  - `list/`：未经修改的列表 HTML
  - `details/`：未经修改的岗位详情 HTML
  - `metadata.json`：URL、时间、状态码、响应头、文件路径和 SHA-256
- `raw/360-careers/<run_id>/`
  - `list/`：未经修改的列表 JSON
  - `details/`：未经修改的岗位详情 JSON
  - `metadata.json`：URL、时间、状态码、响应头、文件路径和 SHA-256
- `normalized/<run_id>/`：解析后的规范化岗位，仅用于核对，不替代原始响应
- `replay/original/`：用于制作回放的原始真实快照
- `replay/scenarios/`：明确标注为 replay 的修改快照和清单
- `runs/`：每次来源执行的机器可读运行报告
- `screenshots/`：必要的页面操作证据；截图不替代原始 HTML/JSON
- `reports/`：关键场景测试结果和汇总报告
- `templates/`：题目附件提供的空表、Schema 和说明
- 整个 `evidence/` 绑定挂载到后端容器的 `/evidence`；真实材料按上述目录直接落在宿主机并可纳入 Git。

任何原始 HTML/JSON 均按响应原始字节保存，不重编码、不改写。每个文件需要在 metadata 和 CSV 中记录相对路径与 SHA-256。
