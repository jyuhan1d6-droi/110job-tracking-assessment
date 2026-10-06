# 最终真实采集验证

验证时间：2026-10-06（记录时间采用 UTC）

本报告仅记录最终两次 `mode=live` 的真实采集。回放运行、自动化测试数据库和第十四步隔离夹具均未计入。

## 最终运行

| 来源 | 类型 | run ID | 状态 | 候选 | 有效 | 新增 | 变化 | 未变化 | 失败 |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| 实习僧 | recruitment_platform | `3b2699b4-e61e-4f24-b3d8-5b91e324d034` | success | 60 | 10 | 2 | 0 | 8 | 0 |
| 360 招聘 | company_careers | `8498d8d5-799c-478e-b88b-675bdeebd4a8` | success | 25 | 25 | 0 | 0 | 25 | 0 |

两次运行均满足 `valid_count = new_count + changed_count + unchanged_count`。实习僧新增 2 条来自最终公开页面中的新稳定 identity；没有使用标题拼接、回放或手写数据补足数量。

## identity 与详情链接

- 实习僧：10 个 observation、10 个不同 `shixiseng:{inn_id}`、10 个不同 HTTPS 详情链接。
- 360 招聘：25 个 observation、25 个不同 `360-careers:{id}`、25 个不同 HTTPS 详情链接。
- 两个来源均没有无效详情链接，也没有同一来源内重复 identity。

## 原始文件核验

| 来源 | 列表文件 | 详情文件 | 合计文件 | 合计字节 | 大小不匹配 | SHA-256 不匹配 |
|---|---:|---:|---:|---:|---:|---:|
| 实习僧 | 3 HTML | 10 HTML | 13 | 7,361,446 | 0 | 0 |
| 360 招聘 | 1 JSON | 25 JSON | 26 | 41,434 | 0 | 0 |

对 39 个文件逐一从磁盘重新读取字节长度并计算 SHA-256，与 `collection_artifacts` 记录比较，全部一致。逐文件路径、大小、哈希、HTTP 状态和抓取时间见 `evidence/reports/final-live-artifacts.csv`。

## CSV 交叉检查

填写完成后重新运行隔离 PostgreSQL 验收套件：42 项全部通过，1 条第三方依赖弃用警告，无失败。

- `collection-runs.csv`：正式填写 2 行，分别对应上述最终 live run；运行统计与数据库一致。
- `source-evidence.csv`：正式填写 2 行；每个来源至少 3 个样例详情链接，并关联最终列表原始文件及 SHA-256。
- `test-cases.csv`：JOB-01 更新为最终 live 数据和本报告；JOB-02 至 JOB-09 的断言仍与最终数据库行为一致，不把本次实习僧新增 2 条误写成“完全相同的重复采集”。

交叉检查的数据库信号：

- 两个最终 live run 都没有创建 change set 或 watch event；360 的 25 条全部为 unchanged，符合 JOB-02。实习僧本次真实出现 2 个新 identity，因此没有把它误判为“完全相同”的重复刷新。
- 360 最终结果内有 7 个标题同为“销售经理”的岗位，7 个 identity 均不同，符合 JOB-03。
- 三个账号各保留 1 个筛选方案；三个账号的关注与动态分别关联各自 user_id，正式回放产生的动态总数为 9，符合 JOB-04 至 JOB-06、JOB-08 和 JOB-09 的数据前提。
- 正式库保留 1 条 `REPLAY_SOURCE_FAILURE` 来源级失败记录，且两个来源此后的最终 live run 均成功，符合 JOB-07 的失败隔离结论。

## 第十六步收口结果

- 299 条反复登录验证产生的认证 session 已清空；业务数据和 evidence 不依赖 session 历史。
- 三条阶段性命名的筛选方案保留原 ID、用户归属和条件，统一改名为“AI 北京岗位”，并同步筛选验证报告。
- 第十四步隔离卷 `job-tracker-step14_postgres_data` 已删除；正式 PostgreSQL 卷未修改。
- `evidence/README.md` 已按实际扁平 artifact 结构修正。
- `evidence/templates/SHA256SUMS` 继续原样保留为附件原文件校验；仓库根目录另行生成 `FINAL_SHA256SUMS` 作为最终提交材料校验。
