import { useQuery } from "@tanstack/react-query";
import { Alert, Button, Card, Empty, Pagination, Skeleton, Space, Typography } from "antd";
import { Link, useSearchParams } from "react-router-dom";
import { fetchWatches } from "../api/watches";
import JobCard from "../components/JobCard";

export default function WatchesPage() {
  const [params, setParams] = useSearchParams();
  const page = Math.max(1, Number(params.get("page") || 1) || 1);
  const query = useQuery({ queryKey: ["watches", page], queryFn: () => fetchWatches(page) });

  return <Space direction="vertical" size="large" className="full-width">
    <div><Typography.Title>我的关注</Typography.Title><Typography.Paragraph type="secondary">只显示当前正在关注的岗位；取消关注不会删除过去的关注区间。</Typography.Paragraph></div>
    {query.isLoading && <Card><Skeleton active paragraph={{ rows: 6 }} /></Card>}
    {query.isError && <Alert type="error" showIcon message="加载关注列表失败" action={<Button onClick={() => query.refetch()}>重试</Button>} />}
    {query.data?.total === 0 && <div className="empty-panel"><Empty description="还没有关注岗位" /><Link to="/jobs"><Button type="primary">前往岗位列表</Button></Link></div>}
    {query.data && query.data.total > 0 && <>
      <Typography.Text>当前关注 {query.data.total} 个岗位</Typography.Text>
      <Space direction="vertical" size="middle" className="full-width">
        {query.data.items.map(item => <div key={item.watch_id}>
          <Typography.Text type="secondary">关注时间：{new Date(item.watched_at).toLocaleString("zh-CN")}</Typography.Text>
          <JobCard job={item.job} />
        </div>)}
      </Space>
      <Pagination current={query.data.page} pageSize={query.data.page_size} total={query.data.total} showSizeChanger={false} onChange={next => setParams(next > 1 ? { page: String(next) } : {})} />
    </>}
  </Space>;
}
