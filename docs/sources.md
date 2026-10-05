# 数据来源

## 实习僧

- 类型：`recruitment_platform`
- 列表入口：`https://www.shixiseng.com/interns/`
- identity：`shixiseng:{inn_id}`
- 采集方式：公开 HTML 列表与详情页
- 原始材料：列表 HTML、详情 HTML、请求元数据和 SHA-256

## 360 招聘

- 类型：`company_careers`
- 官方入口：`https://hr.360.cn/hr/list`
- identity：`360-careers:{id}`
- 采集方式：官方页面使用的公开 JSON 列表与详情接口
- 原始材料：列表 JSON、详情 JSON、请求元数据和 SHA-256

两个来源缺失的截止时间和招聘状态均保留为 `null`，界面显示“未提供”。来源不得静默切换；出现访问、解析或数量问题时应记录失败并报告。

