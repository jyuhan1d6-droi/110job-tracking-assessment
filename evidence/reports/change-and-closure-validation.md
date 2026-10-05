# 字段变化与明确关闭规则验证

本次使用事务内测试数据验证变化链路，测试结束后全部回滚，没有修改真实采集岗位。未执行回放功能。

## 跟踪字段

只比较以下三个字段：

- `requirements`
- `deadline`
- `recruitment_status`

岗位名称、公司、城市、详情链接或原始页面外围内容变化不会建立 `job_change_sets`。

## 变化记录

- 首次观察只建立岗位及 observation，不建立 change set。
- 内容未变化时建立本次 observation，并计入 `unchanged_count`。
- 一次采集中多个字段变化时，只建立一个 change set，每个实际变化字段建立一条 field change。
- 已验证岗位要求、截止日期和招聘状态同时变化时，产生一个 change set 和三条字段明细。
- 已验证 A→B→A 会产生两次独立变化，不因内容哈希曾经出现过而吞掉第二次变化。

## 明确关闭

关闭写入必须同时满足：

- `recruitment_status = closed`
- `explicit_closed = true`
- 非空 `closed_evidence_text`
- 对应详情原始证据 artifact

360 仅接受明确的状态字段值，或接口明确返回“已下架”“已结束”“停止招聘”“已关闭”。实习僧仅接受页面正文明确出现相同关闭语义。

以下情况不会记录关闭：

- 岗位没有出现在某次列表中
- 页面结构缺失
- 页面暂时无法访问
- HTTP 请求失败
- 未识别或含糊的状态值
- 仅有 `closed` 值但没有明确证据文本

已验证带明确“该职位已下架”证据时，observation 保存关闭状态、明确关闭标记和证据文本，并只生成 `recruitment_status` 字段变化。没有证据的关闭写入会在服务层被拒绝，数据库约束继续作为第二道保护。
