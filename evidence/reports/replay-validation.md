# 基于真实快照的本地回放验证

验证日期：2026-10-06

## 官方格式兼容

清单：`evidence/replay/scenarios/shixiseng-secretary/replay.json`

校验 Schema：题目附件原文件 `evidence/templates/replay.schema.json`，JSON Schema 2020-12。

清单包含附件规定的 `schemaVersion=1.0`、`mode=replay`、`provenance` 和 `steps`，四个步骤均通过官方 Schema 校验。`steps[].changes` 只进入证据元数据供人工复核，不参与岗位写入或变化判定；实际变化由应用解析 `snapshotFile` 后与 `jobs` 当前值比较产生。

## 真实证据来源

- 来源：实习僧
- 真实岗位：秘书
- 稳定身份：`shixiseng:inn_9g4ply6sfzje`
- 原始 URL：`https://www.shixiseng.com/intern/inn_9g4ply6sfzje`
- 原始 HTML：`raw/shixiseng/fb11537c-bed7-422b-bf91-059b3b287c0b/detail-inn_9g4ply6sfzje.html`
- 原始 SHA-256：`6caadf4d9d5d687bee016907eda428460c8d7cfb24ca94bf314fd86268218723`

原始文件哈希与数据库 artifact 一致。派生快照保留 identity、标题、公司、城市和原始链接，原始 HTML 未被修改。

## 执行结果

| 顺序 | 步骤 | 运行 ID | 状态 | changed | unchanged | failed_count |
|---|---|---|---|---:|---:|---:|
| 1 | baseline | `e7ff552d-aa5c-4f75-9460-eb9dbd32bf21` | success | 0 | 1 | 0 |
| 2 | requirements-change | `439607b2-448b-4413-a921-21d939480b2a` | success | 1 | 0 | 0 |
| 3 | requirements-change 重复 | `45adea1f-6eae-4128-a5c1-729f9c05828a` | success | 0 | 1 | 0 |
| 4 | explicit-close | `06d70a42-101f-43a7-92e7-c0e1e7c84aed` | success | 1 | 0 | 0 |
| 5 | source-failure | `4e1a8edf-d0bf-42a8-8363-86213c54ac49` | failed | 0 | 0 | 0 |
| 6 | baseline 恢复 | `8a76ad7e-d4e3-450b-a02d-c7def8ad95e1` | success | 1 | 0 | 0 |

来源级失败没有具体岗位失败，按要求 `failed_count=0`。失败运行没有修改岗位、建立变化或动态。

## 实际比较结果

数据库实际产生的回放字段变化：

- 要求变化运行：仅 `requirements`
- 明确关闭运行：仅 `recruitment_status`
- 基线恢复：`requirements` 与 `recruitment_status`
- 重复要求快照：无 change set

这证明业务结果来自快照解析和当前值比较，而不是读取清单中的声明答案。

## 关注动态

三个账号都在关注目标岗位。要求变化、明确关闭和基线恢复各为三个账号产生一条 `origin=replay` 动态：

- `jobseeker1`：3 条
- `jobseeker2`：3 条
- `maintainer`：3 条

页面和接口均显示“本地回放”。

## 最终状态

执行明确关闭验证后重新执行 baseline：

- 岗位要求恢复为真实基线
- 招聘状态恢复为未提供
- `last_live_seen_at` 保持 `2026-10-05T17:41:29.848845+00:00`
- 最近更新模式为 `replay`
- 原始岗位链接保持不变

回放没有覆盖最近真实采集时间，也没有冒充新的真实抓取。
