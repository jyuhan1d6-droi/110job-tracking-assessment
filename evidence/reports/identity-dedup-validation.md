# Identity、规范化与重复采集验证

本次未主动修改岗位字段、制造关闭状态或使用回放数据。验证由自动化约束测试及各来源一次真实重复采集组成。

## 360 招聘

- 重复运行 ID：`6f032173-cc67-493d-96a0-34f1a8622971`
- 状态：`success`
- 列表发现：25
- 有效岗位：25
- 新增：0
- 变化：0
- 未变化：25
- 失败：0
- 运行后岗位总数：25
- distinct identity：25
- 本次 observation：25
- 本次 change set：0
- 原始证据：`evidence/raw/360-careers/6f032173-cc67-493d-96a0-34f1a8622971/`
- 证据文件：26 个，共 41,434 字节，SHA-256 差异数 0

数据库中的 7 个“销售经理”岗位拥有 7 个不同的 `external_identity`，均保持为独立岗位。

## 实习僧

- 重复运行 ID：`ae8a09d3-c53f-459b-ae69-54ca2976252e`
- 状态：`success`
- 列表候选：60
- 有效岗位：10
- 新增：0
- 变化：0
- 未变化：10
- 失败：0
- 运行后岗位总数：10
- distinct identity：10
- 本次 observation：10
- 本次 change set：0
- 原始证据：`evidence/raw/shixiseng/ae8a09d3-c53f-459b-ae69-54ca2976252e/`
- 证据文件：13 个，共 7,351,087 字节，SHA-256 差异数 0

实习僧详情链接中的跟踪查询参数不参与 identity，规范化详情链接固定为 `https://www.shixiseng.com/intern/{inn_id}`。

## 自动化验证

- 同一来源、相同 identity 受数据库唯一约束保护。
- 360 使用 `360-careers:{id}`；实习僧使用 `shixiseng:{inn_id}`。
- 两个来源都验证了同名但不同 ID 会得到两个独立 identity 和两条岗位记录。
- 等价换行和连续空白规范化后得到相同要求文本及内容哈希。
- 重复采集仍建立本次 observation，但不会建立重复岗位或虚假 change set。
