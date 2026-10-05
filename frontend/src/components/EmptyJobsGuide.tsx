import { Button, Empty, Typography } from "antd";
import type { CurrentUser } from "../types/jobs";

export default function EmptyJobsGuide({ user }: { user: CurrentUser }) {
  return <div className="empty-panel">
    <Empty description="当前还没有采集到岗位" />
    {user.role === "maintainer"
      ? <><Typography.Paragraph>请先使用数据维护功能采集实习僧和 360 招聘岗位。</Typography.Paragraph><Button disabled>数据采集入口将在维护页面提供</Button></>
      : <Typography.Paragraph>请联系数据维护账号完成首次采集。</Typography.Paragraph>}
  </div>;
}
