import { Typography } from "antd";
import type { ChangedField } from "../types/watchEvents";

export const fieldLabels: Record<ChangedField["field_name"], string> = {
  requirements: "岗位要求",
  deadline: "截止时间",
  recruitment_status: "招聘状态",
};

export function displayChangeValue(field: ChangedField["field_name"], value: string | null) {
  if (value === null || value === "") return "未提供";
  if (field === "recruitment_status") {
    if (value === "open") return "招聘中";
    if (value === "closed") return "已关闭";
  }
  return value;
}

export default function ChangeValue({ field, value }: { field: ChangedField["field_name"]; value: string | null }) {
  return <Typography.Paragraph className="change-value">{displayChangeValue(field, value)}</Typography.Paragraph>;
}
