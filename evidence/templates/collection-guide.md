# 采集记录与来源证据

## 怎样填写

每个来源每次运行填一行 `collection-runs.csv`；每个来源填一行 `source-evidence.csv`。两类来源各至少 10 个有效岗位，不能将招聘平台的企业主页当成大厂官方招聘网站。

| 字段 | 说明 |
|---|---|
| run_id / source_id | 自定唯一标识；同一次运行、同一来源保持一致 |
| source_type | `recruitment_platform` 或 `company_careers` |
| entry_url / source_name | 实际访问地址与来源名称 |
| company_official_evidence_url | 官方站填公司官网指向招聘入口等可核对依据；招聘平台可留空 |
| started_at / finished_at / collected_at | 含时区的 ISO 8601 时间 |
| status | `success`、`partial`、`failed`；失败也保留一行 |
| http_status | 实际响应状态码；无响应留空 |
| fetched_count / valid_count | 抓到的条目数 / 去重后成功解析的有效岗位数 |
| new_count / changed_count / unchanged_count | 成功处理岗位的新增 / 更新 / 无变化数量；三项合计应等于 valid_count |
| failed_count | 抓取到但解析或保存失败的条目数；来源级请求失败另填 error，不虚构条目数 |
| raw_snapshot_path / snapshot_path | 提交材料中的相对路径，保留实际页面或响应；不只交截图结论 |
| raw_sha256 / snapshot_sha256 | 对相应文件原始字节计算 SHA-256 |
| error_code / error_message | 实际失败原因；成功留空，不把失败写成空列表成功 |
| valid_unique_jobs | 本来源去重后有效岗位数；不是历次运行数量累加 |
| sample_detail_urls | 多条详情链接以英文分号分隔 |
| collection_method | 公开页面 / 公开接口 / 浏览器自动化及入口位置 |
| access_notes | 访问条件、分页方法、请求间隔等复现说明 |

岗位证据至少能对应名称、来源身份、详情链接及采集时间。来源未公开的截止日期、招聘状态保留空值，界面显示“未提供”。同名岗位是否同一条由来源和稳定 ID（或规范化详情 URL）决定，不由标题决定。

## 复核步骤

1. 从应用发起两类来源采集，核对来源各不少于 10 条。
2. 随机打开至少 2 条/来源的详情链接，与快照及应用内容核对。
3. 重复采集，核对有效岗位去重、无变化不产生日志。
4. 保存采集日志与原始文件；随后再按回放格式验证变更。不能用回放代替上述真实采集。
