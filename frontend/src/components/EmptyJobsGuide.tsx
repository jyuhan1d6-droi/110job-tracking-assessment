import { Button, Empty, Typography } from "antd";
import { Link } from "react-router-dom";
import type { CurrentUser } from "../types/jobs";

export default function EmptyJobsGuide({ user }: { user: CurrentUser }) {
  return <div className="empty-panel">
    <Empty description="当前还没有采集到岗位" />
    {user.role === "maintainer"
      ? <><Typography.Paragraph>请先使用数据维护功能采集实习僧和 360 招聘岗位。</Typography.Paragraph><Link to="/maintenance/collection"><Button type="primary">前往数据采集</Button></Link></>
      : <Typography.Paragraph>请联系数据维护账号完成首次采集。</Typography.Paragraph>}
  </div>;
}
