import { useQuery } from "@tanstack/react-query";
import { Alert, Button, Card, Empty, Pagination, Skeleton, Space, Tag, Typography } from "antd";
import { Link, useSearchParams } from "react-router-dom";
import { fetchWatchEvents } from "../api/watchEvents";
import { fieldLabels } from "../components/ChangeValue";

export default function WatchEventsPage() {
  const [params, setParams] = useSearchParams();
  const page = Math.max(1, Number(params.get("page") || 1) || 1);
  const query = useQuery({ queryKey: ["watch-events", page], queryFn: () => fetchWatchEvents(page) });
  return <Space direction="vertical" size="large" className="full-width">
    <div><Typography.Title>关注动态</Typography.Title><Typography.Paragraph type="secondary">只记录关注期间发生的岗位变化，不补发关注前或取消期间的变化。</Typography.Paragraph></div>
    {query.isLoading && <Card><Skeleton active paragraph={{ rows: 8 }} /></Card>}
    {query.isError && <Alert type="error" showIcon message="加载关注动态失败" action={<Button onClick={() => query.refetch()}>重试</Button>} />}
    {query.data?.total === 0 && <div className="empty-panel"><Empty description="当前还没有关注期间发生的岗位变化" /><Typography.Paragraph>关注岗位本身不会补发关注前的历史变化。</Typography.Paragraph><Link to="/watches"><Button type="primary">查看我的关注</Button></Link></div>}
    {query.data && query.data.total > 0 && <>
      <Typography.Text>共 {query.data.total} 条关注动态</Typography.Text>
      <Space direction="vertical" size="middle" className="full-width">{query.data.items.map(event => <Card key={event.id} className="job-card">
        <Space direction="vertical" className="full-width">
          <div className="job-card-heading"><div><Typography.Title level={3}>{event.title}</Typography.Title><Typography.Text type="secondary">{event.company} · {event.city}</Typography.Text></div><Tag>{event.source.name}</Tag></div>
          <Space wrap>{event.changed_fields.map(field => <Tag color="orange" key={field}>{fieldLabels[field]}</Tag>)}</Space>
          <Typography.Text>发生 {event.change_count} 项变化 · {new Date(event.detected_at).toLocaleString("zh-CN")}</Typography.Text>
          <Space><Link to={`/watch-events/${event.id}`}><Button type="primary">查看变化详情</Button></Link><Link to={`/jobs/${event.job_id}`}><Button>查看岗位</Button></Link></Space>
        </Space>
      </Card>)}</Space>
      <Pagination current={query.data.page} pageSize={query.data.page_size} total={query.data.total} showSizeChanger={false} onChange={next => setParams(next > 1 ? { page: String(next) } : {})} />
    </>}
  </Space>;
}
