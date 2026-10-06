import { useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { Alert, Button, Card, Empty, Form, Input, Pagination, Select, Skeleton, Space, Typography } from "antd";
import { useSearchParams } from "react-router-dom";
import { fetchCities, fetchJobs, fetchJobSummary } from "../api/jobs";
import { useAuth } from "../auth/AuthContext";
import EmptyJobsGuide from "../components/EmptyJobsGuide";
import JobCard from "../components/JobCard";
import SavedFiltersPanel, { buildSavedFilterParams } from "../components/SavedFiltersPanel";

type SearchValues = { keyword?: string; city?: string };

export function emptyMode(totalVisibleJobs: number | undefined, filteredTotal: number | undefined) {
  if (totalVisibleJobs === 0) return "first-use";
  if ((totalVisibleJobs ?? 0) > 0 && filteredTotal === 0) return "filtered-empty";
  return "results";
}

export default function JobsPage() {
  const { user } = useAuth();
  const [params, setParams] = useSearchParams();
  const keyword = params.get("keyword") ?? "";
  const city = params.get("city") ?? "";
  const page = Math.max(1, Number(params.get("page") || 1) || 1);
  const activeSavedFilter = params.get("savedFilter") ?? "";
  const [form] = Form.useForm<SearchValues>();
  useEffect(() => { form.setFieldsValue({ keyword, city: city || undefined }); }, [form, keyword, city]);

  const jobs = useQuery({ queryKey: ["jobs", keyword, city, page], queryFn: () => fetchJobs({ keyword, city, page }) });
  const summary = useQuery({ queryKey: ["job-summary"], queryFn: fetchJobSummary });
  const cities = useQuery({ queryKey: ["job-cities"], queryFn: fetchCities });

  function apply(values: SearchValues) {
    const next: Record<string, string> = {};
    if (values.keyword?.trim()) next.keyword = values.keyword.trim();
    if (values.city?.trim()) next.city = values.city.trim();
    setParams(next);
  }

  function changePage(nextPage: number) {
    const next = new URLSearchParams(params);
    if (nextPage > 1) next.set("page", String(nextPage)); else next.delete("page");
    setParams(next);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  const mode = emptyMode(summary.data?.total_visible_jobs, jobs.data?.total);
  return <Space direction="vertical" size="large" className="full-width">
    <div><Typography.Title>岗位</Typography.Title><Typography.Paragraph type="secondary">从实习僧和 360 招聘的真实采集数据中查找岗位。</Typography.Paragraph></div>
    <Card>
      <Form<SearchValues> form={form} layout="inline" onFinish={apply} className="search-form">
        <Form.Item name="keyword"><Input allowClear placeholder="岗位名称或岗位要求" /></Form.Item>
        <Form.Item name="city"><Select allowClear showSearch placeholder="选择城市" loading={cities.isLoading} options={(cities.data ?? []).map(value => ({ value, label: value }))} /></Form.Item>
        <Form.Item><Space><Button type="primary" htmlType="submit">搜索</Button><Button onClick={() => { form.resetFields(); setParams({}); }}>清空</Button></Space></Form.Item>
      </Form>
      {cities.isError && <Alert className="inline-alert" type="warning" message="城市选项暂时不可用，仍可使用关键词搜索。" />}
    </Card>

    <SavedFiltersPanel
      keyword={keyword}
      city={city}
      activeId={activeSavedFilter}
      onUse={filter => setParams(buildSavedFilterParams(filter))}
      onDeletedActive={() => {
        const next = new URLSearchParams(params);
        next.delete("savedFilter");
        setParams(next);
      }}
    />

    {(jobs.isError || summary.isError) && <Alert type="error" showIcon message="加载岗位失败" description="请检查服务状态后重试。" action={<Button onClick={() => { jobs.refetch(); summary.refetch(); }}>重试</Button>} />}
    {(jobs.isLoading || summary.isLoading) && <Card><Skeleton active paragraph={{ rows: 6 }} /></Card>}
    {!jobs.isLoading && !summary.isLoading && mode === "first-use" && user && <EmptyJobsGuide user={user} />}
    {!jobs.isLoading && !summary.isLoading && mode === "filtered-empty" && <div className="empty-panel"><Empty description="未找到符合条件的岗位" /><Typography.Paragraph>请调整关键词或城市。</Typography.Paragraph><Button onClick={() => { form.resetFields(); setParams({}); }}>清空筛选</Button></div>}
    {jobs.data && jobs.data.total > 0 && <>
      <Typography.Text>共 {jobs.data.total} 个岗位</Typography.Text>
      <Space direction="vertical" size="middle" className="full-width">{jobs.data.items.map(job => <JobCard key={job.id} job={job} />)}</Space>
      <Pagination current={jobs.data.page} pageSize={jobs.data.page_size} total={jobs.data.total} showSizeChanger={false} onChange={changePage} />
    </>}
  </Space>;
}
