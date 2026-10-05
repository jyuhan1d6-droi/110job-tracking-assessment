# 岗位搜索与变更追踪 · 附件

先查看 `collection-guide.md`，用两个真实来源完成采集，再填写记录。这里不含岗位数据，也不指定招聘来源。

| 文件 | 用途 |
|---|---|
| collection-runs.csv | 每次、每个来源的采集执行记录，空模板 |
| source-evidence.csv | 两类来源的真实性与岗位数量证据，空模板 |
| collection-guide.md | 记录字段和证据要求 |
| replay-format.md / replay.schema.json | 基于自己真实快照制作回放的格式 |
| replay-empty.json | 空回放清单，仅供填写，未填完整不能作为验收资料 |
| test-cases.csv | 变更、关注、去重与失败场景 |

CSV 为 UTF-8（带 BOM），可用 Excel 打开。回放格式是材料交换格式，不限制应用内部表结构，也不要求另做回放管理后台。
