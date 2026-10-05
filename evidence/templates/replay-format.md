# 变更回放格式

回放用于模拟短时间内网站没有发生的变化。所有回放必须从候选人真实抓取的快照复制修改；原始文件单独保留。界面和证据明确标为“回放”，不得宣称是新抓取的数据。

`replay-empty.json` 是待填写的空模板；`replay.schema.json` 使用 JSON Schema 2020-12，填写后的材料应符合结构。系统无需按此设计数据库。

## 清单字段

| 字段 | 含义 |
|---|---|
| schemaVersion | 固定 `1.0` |
| mode | 固定 `replay` |
| provenance | 真实来源 ID、URL、采集时间、原快照相对路径和 SHA-256 |
| steps[].stepId | 场景中的唯一步骤 ID |
| steps[].kind | `snapshot`（快照）、`source_failure`（来源失败） |
| snapshotFile / sha256 | 该步骤快照文件与校验值；失败步骤不提供 |
| failureReason | 失败步骤填写明确原因 |
| changes | 回放人为修改的条目及前后值；无变化时空数组 |
| expected | 预期的岗位及关注动态变化，用文字说明 |

每个快照 JSON 的结构为 `{ "sourceId": "自定来源ID", "jobs": [] }`。`jobs` 中各条至少包含 `identity`、`title`、`company`、`city`、`requirements`、`deadline`、`status`、`detailUrl`；其中 identity 是来源稳定 ID 或规范化详情 URL，deadline/status 可为 null。修改 status 为 closed 时需在回放中加 `explicitClosedEvidence` 说明模拟的明确关闭证据。真实采集也必须有来源明确关闭证据，不能只因列表缺失判关。

## 推荐步骤顺序

1. 用原始真实快照建立初始岗位，此时不产生变更动态。
2. 让账号 A 关注其中岗位，再复制快照，只修改该岗位的 requirements；changes 写明 identity、field、before、after。
3. 重复加载同一文件，不新增变更。
4. 从列表快照删去该岗位：现有岗位保留，不自动关闭。
5. 使用 source_failure 步骤模拟该来源超时：保留岗位，另一个来源可继续。
6. 复制原快照，模拟来源明确关闭：记录旧新状态和依据；A 收到动态。
7. A 取消关注，再改变截止时间：旧动态可保留，不向 A 新增动态。稍后关注不补发关注之前的变更。

`changes`、文件 hash 与 expected 是复核材料，不能作为直接写入业务结果的“答案”。应用仍须自己比较快照并执行变更规则。
