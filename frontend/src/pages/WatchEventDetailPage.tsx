import { useQuery } from "@tanstack/react-query";
import { Alert, Button, Card, Descriptions, Result, Skeleton, Space, Tag, Typography } from "antd";
import axios from "axios";
import { Link, useParams } from "react-router-dom";
import { fetchWatchEvent } from "../api/watchEvents";
import ChangeValue, { fieldLabels } from "../components/ChangeValue";

export default function WatchEventDetailPage() {
  const { eventId = "" } = useParams();
  const query = useQuery({ queryKey: ["watch-event", eventId], queryFn: () => fetchWatchEvent(eventId), retry: false });
  if (query.isLoading) return <Card><Skeleton active paragraph={{ rows: 10 }} /></Card>;
  if (query.isError) {
    const missing = axios.isAxiosError(query.error) && query.error.response?.status === 404;
    if (missing) return <Result status="404" title="关注动态不存在" extra={<Link to="/watch-events"><Button>返回关注动态</Button></Link>} />;
    return <Alert type="error" showIcon message="加载变化详情失败" action={<Button onClick={() => query.refetch()}>重试</Button>} />;
  }
  const event = query.data!;
  return <Space direction="vertical" size="large" className="full-width">
    <Link to="/watch-events">← 返回关注动态</Link>
    <Card>
      <Typography.Title>{event.title}</Typography.Title>
      <Descriptions bordered column={{ xs: 1, md: 2 }}>
        <Descriptions.Item label="公司">{event.company}</Descriptions.Item><Descriptions.Item label="城市">{event.city}</Descriptions.Item>
        <Descriptions.Item label="变化时间">{new Date(event.detected_at).toLocaleString("zh-CN")}</Descriptions.Item><Descriptions.Item label="变化来源">{event.origin === "live" ? "真实采集" : "本地回放"}</Descriptions.Item>
        <Descriptions.Item label="岗位来源">{event.source.name}</Descriptions.Item><Descriptions.Item label="变化数量">{event.change_count}</Descriptions.Item>
      </Descriptions>
      <Space className="detail-actions"><Link to={`/jobs/${event.job_id}`}><Button type="primary">查看当前岗位</Button></Link><Button href={event.detail_url} target="_blank" rel="noopener noreferrer">查看原岗位</Button></Space>
    </Card>
    {event.changes.map(change => <Card key={change.field_name} title={<Space><Tag color="orange">变化</Tag>{fieldLabels[change.field_name]}</Space>}>
      <div className="change-comparison"><div><Typography.Title level={5}>修改前</Typography.Title><ChangeValue field={change.field_name} value={change.before_text} /></div><div><Typography.Title level={5}>修改后</Typography.Title><ChangeValue field={change.field_name} value={change.after_text} /></div></div>
    </Card>)}
  </Space>;
}
