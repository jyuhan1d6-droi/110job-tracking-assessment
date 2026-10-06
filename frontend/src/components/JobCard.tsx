import { Button, Card, Descriptions, Space, Tag, Typography } from "antd";
import { Link, useLocation } from "react-router-dom";
import type { JobListItem } from "../types/jobs";
import WatchButton from "./WatchButton";

export function displayStatus(job: Pick<JobListItem, "status_provided" | "recruitment_status">) {
  if (!job.status_provided) return "未提供";
  return job.recruitment_status === "closed" ? "已关闭" : "招聘中";
}

export default function JobCard({ job }: { job: JobListItem }) {
  const location = useLocation();
  return <Card className="job-card">
    <Space direction="vertical" size="middle" className="full-width">
      <div className="job-card-heading">
        <div><Typography.Title level={3}>{job.title}</Typography.Title><Typography.Text type="secondary">{job.company}</Typography.Text></div>
        <Space wrap><Tag color="blue">{job.city}</Tag><Tag>{job.source.name}</Tag>{job.last_update_mode === "replay" && <Tag color="purple">本地回放数据</Tag>}<Tag color={job.recruitment_status === "closed" ? "red" : "default"}>{displayStatus(job)}</Tag></Space>
      </div>
      <Typography.Paragraph className="requirements-summary">{job.requirements_summary}</Typography.Paragraph>
      <Descriptions size="small" column={{ xs: 1, sm: 2 }}>
        <Descriptions.Item label="截止时间">{job.deadline_provided ? job.deadline_raw : "未提供"}</Descriptions.Item>
        <Descriptions.Item label="最近真实采集">{job.last_live_seen_at ? new Date(job.last_live_seen_at).toLocaleString("zh-CN") : "暂无"}</Descriptions.Item>
        <Descriptions.Item label="最近回放处理">{job.last_replay_seen_at ? new Date(job.last_replay_seen_at).toLocaleString("zh-CN") : "未回放"}</Descriptions.Item>
      </Descriptions>
      <Space>
        <Link to={`/jobs/${job.id}`} state={{ from: `${location.pathname}${location.search}` }}><Button type="primary">查看详情</Button></Link>
        <Button href={job.detail_url} target="_blank" rel="noopener noreferrer">原岗位</Button>
        <WatchButton jobId={job.id} isWatched={job.is_watched} />
      </Space>
    </Space>
  </Card>;
}
