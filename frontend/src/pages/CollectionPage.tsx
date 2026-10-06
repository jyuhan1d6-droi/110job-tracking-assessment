import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Alert, Button, Card, Descriptions, Drawer, Pagination, Select, Space, Spin, Table, Tag, Typography, message } from "antd";
import axios from "axios";
import { useState } from "react";
import { fetchCollectionRun, fetchCollectionRuns, fetchCollectionSources, fetchRunArtifacts, startCollection } from "../api/collection";
import type { CollectionRun } from "../types/collection";

const labels: Record<string, string> = { pending: "等待执行", running: "采集中", success: "成功", partial: "部分成功", failed: "失败" };
const colors: Record<string, string> = { pending: "default", running: "processing", success: "success", partial: "warning", failed: "error" };
function RunStatus({ status }: { status: string }) { return <Tag color={colors[status]}>{labels[status] ?? status}</Tag>; }
function errorText(error: unknown) { return axios.isAxiosError(error) ? String(error.response?.data?.detail ?? error.message) : "操作失败"; }

export default function CollectionPage() {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [sourceFilter, setSourceFilter] = useState<string>();
  const [statusFilter, setStatusFilter] = useState<string>();
  const [selected, setSelected] = useState<string>();
  const [artifactPage, setArtifactPage] = useState(1);
  const sources = useQuery({ queryKey: ["collection-sources"], queryFn: fetchCollectionSources, refetchInterval: query => query.state.data?.some(item => item.active_run) ? 2000 : 10000 });
  const runs = useQuery({ queryKey: ["collection-runs", page, sourceFilter, statusFilter], queryFn: () => fetchCollectionRuns({ page, source_code: sourceFilter, status: statusFilter }), refetchInterval: 3000 });
  const detail = useQuery({ queryKey: ["collection-run", selected], queryFn: () => fetchCollectionRun(selected!), enabled: !!selected, refetchInterval: query => ["pending", "running"].includes(query.state.data?.status ?? "") ? 2000 : false });
  const artifacts = useQuery({ queryKey: ["collection-artifacts", selected, artifactPage], queryFn: () => fetchRunArtifacts(selected!, artifactPage), enabled: !!selected });
  const trigger = useMutation({
    mutationFn: startCollection,
    onSuccess: run => { message.success(`${run.source_name} 已开始真实采集`); queryClient.invalidateQueries({ queryKey: ["collection-sources"] }); queryClient.invalidateQueries({ queryKey: ["collection-runs"] }); setSelected(run.id); },
    onError: error => message.error(errorText(error)),
  });
  const sourceOptions = (sources.data ?? []).map(item => ({ value: item.code, label: item.name }));

  return <Space direction="vertical" size="large" className="full-width">
    <div><Typography.Title>数据采集</Typography.Title><Typography.Paragraph type="secondary">从固定公开来源执行真实采集。原始响应先保存到 evidence，再解析和入库；本页面与本地回放严格分开。</Typography.Paragraph></div>
    {sources.isError && <Alert type="error" showIcon message="来源状态加载失败" description={errorText(sources.error)} action={<Button onClick={() => sources.refetch()}>重试</Button>} />}
    {sources.isLoading && <Card><Spin /></Card>}
    <div className="source-grid">{sources.data?.map(source => {
      const latest = source.active_run ?? source.latest_run;
      return <Card key={source.code} title={<Space><span>{source.name}</span><Tag>{source.source_type === "company_careers" ? "公司官方招聘" : "招聘平台"}</Tag></Space>}>
        <Space direction="vertical" className="full-width">
          <a href={source.entry_url} target="_blank" rel="noreferrer">打开来源网站</a>
          <Typography.Text type="secondary">超时 {source.timeout_seconds}s · 重试 {source.max_retries} 次 · 请求间隔 {source.request_interval_ms}ms</Typography.Text>
          <Typography.Text>最近成功：{source.latest_success_at ? new Date(source.latest_success_at).toLocaleString("zh-CN") : "暂无"}</Typography.Text>
          {latest ? <><Space>最近状态 <RunStatus status={latest.status} /></Space><Typography.Text>新增 {latest.new_count} · 变化 {latest.changed_count} · 未变化 {latest.unchanged_count} · 失败 {latest.failed_count}</Typography.Text>{latest.error_message && <Alert type="error" message={latest.error_message} />}</> : <Typography.Text type="secondary">暂无运行记录</Typography.Text>}
          <Button type="primary" loading={trigger.isPending && trigger.variables === source.code} disabled={!source.enabled || !!source.active_run} onClick={() => trigger.mutate(source.code)}>{source.active_run ? "正在真实采集" : "开始真实采集"}</Button>
        </Space>
      </Card>;
    })}</div>

    <Card title="真实采集运行历史">
      <Space wrap className="history-filters"><Select allowClear placeholder="全部来源" options={sourceOptions} value={sourceFilter} onChange={value => { setSourceFilter(value); setPage(1); }} /><Select allowClear placeholder="全部状态" value={statusFilter} onChange={value => { setStatusFilter(value); setPage(1); }} options={Object.entries(labels).map(([value, label]) => ({ value, label }))} /></Space>
      <Table rowKey="id" loading={runs.isLoading} pagination={false} dataSource={runs.data?.items ?? []} columns={[
        { title: "开始时间", dataIndex: "started_at", render: value => new Date(value).toLocaleString("zh-CN") },
        { title: "来源", dataIndex: "source_name" }, { title: "状态", dataIndex: "status", render: value => <RunStatus status={value} /> },
        { title: "有效", dataIndex: "valid_count" }, { title: "新增", dataIndex: "new_count" }, { title: "变化", dataIndex: "changed_count" },
        { title: "未变化", dataIndex: "unchanged_count" }, { title: "失败", dataIndex: "failed_count" },
        { title: "操作", render: (_: unknown, run: CollectionRun) => <Button onClick={() => { setSelected(run.id); setArtifactPage(1); }}>详情与证据</Button> },
      ]} />
      {!!runs.data?.total && <Pagination current={page} pageSize={20} total={runs.data.total} showSizeChanger={false} onChange={setPage} />}
    </Card>

    <Drawer width={760} title="采集运行详情" open={!!selected} onClose={() => setSelected(undefined)}>
      {detail.isLoading && <Spin />}{detail.isError && <Alert type="error" message="运行详情加载失败" description={errorText(detail.error)} />}
      {detail.data && <Space direction="vertical" size="large" className="full-width"><Descriptions bordered column={2}>
        <Descriptions.Item label="来源">{detail.data.source_name}</Descriptions.Item><Descriptions.Item label="状态"><RunStatus status={detail.data.status} /></Descriptions.Item>
        <Descriptions.Item label="触发账号">{detail.data.triggered_by}</Descriptions.Item><Descriptions.Item label="开始时间">{new Date(detail.data.started_at).toLocaleString("zh-CN")}</Descriptions.Item>
        <Descriptions.Item label="获取/有效">{detail.data.fetched_count} / {detail.data.valid_count}</Descriptions.Item><Descriptions.Item label="新增/变化/未变化/失败">{detail.data.new_count} / {detail.data.changed_count} / {detail.data.unchanged_count} / {detail.data.failed_count}</Descriptions.Item>
        <Descriptions.Item label="错误代码">{detail.data.error_code ?? "无"}</Descriptions.Item><Descriptions.Item label="证据数量">{detail.data.artifact_count}</Descriptions.Item>
      </Descriptions>{detail.data.error_message && <Alert type="error" message="失败原因" description={detail.data.error_message} />}
      <Typography.Title level={4}>原始证据</Typography.Title>
      <Table rowKey="id" size="small" loading={artifacts.isLoading} pagination={false} dataSource={artifacts.data?.items ?? []} columns={[
        { title: "类型", dataIndex: "artifact_type" }, { title: "HTTP", dataIndex: "http_status", render: value => value ?? "—" },
        { title: "大小", dataIndex: "byte_size", render: value => `${value} B` },
        { title: "路径 / SHA-256", render: (_: unknown, item) => <div><Typography.Text copyable>{item.relative_path}</Typography.Text><br /><Typography.Text type="secondary" copyable>{item.sha256}</Typography.Text></div> },
        { title: "操作", render: (_: unknown, item) => <Button href={`/api/collection/artifacts/${item.id}/download`}>下载</Button> },
      ]} />
      {!!artifacts.data?.total && <Pagination current={artifactPage} pageSize={50} total={artifacts.data.total} showSizeChanger={false} onChange={setArtifactPage} />}</Space>}
    </Drawer>
  </Space>;
}
