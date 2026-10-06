import { useQuery } from "@tanstack/react-query";
import { Alert, Button, Card, Descriptions, Result, Skeleton, Space, Tag, Typography } from "antd";
import axios from "axios";
import { Link, useLocation, useParams } from "react-router-dom";
import { fetchJob } from "../api/jobs";
import { displayStatus } from "../components/JobCard";
import WatchButton from "../components/WatchButton";

export default function JobDetailPage() {
  const { jobId = "" } = useParams();
  const location = useLocation();
  const backTo = (location.state as { from?: string } | null)?.from ?? "/jobs";
  const query = useQuery({ queryKey: ["job", jobId], queryFn: () => fetchJob(jobId), retry: false });
  if (query.isLoading) return <Card><Skeleton active paragraph={{ rows: 10 }} /></Card>;
  if (query.isError) {
    const missing = axios.isAxiosError(query.error) && query.error.response?.status === 404;
    if (missing) return <Result status="404" title="岗位不存在" extra={<Link to={backTo}><Button>返回岗位列表</Button></Link>} />;
    return <Alert type="error" showIcon message="岗位详情加载失败" action={<Button onClick={() => query.refetch()}>重试</Button>} />;
  }
  const job = query.data!;
  return <Space direction="vertical" size="large" className="full-width">
    <Link to={backTo}>← 返回岗位列表</Link>
    <Card>
      <Space direction="vertical" size="middle" className="full-width">
        <div><Space wrap><Tag color="blue">{job.city}</Tag><Tag>{job.source.name}</Tag>{job.last_update_mode === "replay" && <Tag color="purple">本地回放数据</Tag>}<Tag color={job.recruitment_status === "closed" ? "red" : "default"}>{displayStatus(job)}</Tag></Space><Typography.Title>{job.title}</Typography.Title><Typography.Title level={4} type="secondary">{job.company}</Typography.Title></div>
        <Descriptions bordered column={{ xs: 1, md: 2 }}>
          <Descriptions.Item label="截止时间">{job.deadline_provided ? job.deadline_raw : "未提供"}</Descriptions.Item>
          <Descriptions.Item label="招聘状态">{displayStatus(job)}</Descriptions.Item>
          <Descriptions.Item label="首次抓取">{new Date(job.first_seen_at).toLocaleString("zh-CN")}</Descriptions.Item>
          <Descriptions.Item label="最近抓取">{new Date(job.last_seen_at).toLocaleString("zh-CN")}</Descriptions.Item>
          <Descriptions.Item label="最近真实采集">{job.last_live_seen_at ? new Date(job.last_live_seen_at).toLocaleString("zh-CN") : "暂无"}</Descriptions.Item>
          <Descriptions.Item label="当前数据来源">{job.last_update_mode === "replay" ? "本地回放" : "真实采集"}</Descriptions.Item>
          <Descriptions.Item label="最近变化">{job.last_changed_at ? new Date(job.last_changed_at).toLocaleString("zh-CN") : "暂无"}</Descriptions.Item>
          <Descriptions.Item label="来源类型">{job.source.source_type === "company_careers" ? "公司官方招聘" : "招聘平台"}</Descriptions.Item>
        </Descriptions>
        <div><Typography.Title level={3}>岗位要求</Typography.Title><Typography.Paragraph className="requirements-full">{job.requirements}</Typography.Paragraph></div>
        <Space><Button type="primary" href={job.detail_url} target="_blank" rel="noopener noreferrer">查看原岗位</Button><WatchButton jobId={job.id} isWatched={job.is_watched} /></Space>
      </Space>
    </Card>
  </Space>;
}
