import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Alert, Button, Card, Descriptions, Empty, message, Space, Tag, Typography } from "antd";
import { fetchReplayScenarios, runReplayScenario } from "../api/replay";
import type { ReplayRun, ReplayScenario } from "../types/replay";

function statusColor(status: string) {
  if (status === "success") return "green";
  if (status === "partial") return "orange";
  return "red";
}

export default function ReplayPage() {
  const queryClient = useQueryClient();
  const scenarios = useQuery({ queryKey: ["replay-scenarios"], queryFn: fetchReplayScenarios });
  const [results, setResults] = useState<Record<string, ReplayRun>>({});
  const mutation = useMutation({
    mutationFn: (scenario: ReplayScenario) => runReplayScenario(scenario.id),
    onSuccess: async (run, scenario) => {
      setResults(current => ({ ...current, [scenario.id]: run }));
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["jobs"] }),
        queryClient.invalidateQueries({ queryKey: ["watches"] }),
        queryClient.invalidateQueries({ queryKey: ["watch-events"] }),
      ]);
      message.success(run.status === "success" ? "本地回放执行完成" : "本地回放按场景返回失败");
    },
    onError: () => message.error("本地回放执行失败，请检查场景校验信息"),
  });

  return <Space direction="vertical" size="large" className="full-width">
    <div><Typography.Title>本地回放</Typography.Title><Alert type="warning" showIcon message="本页面执行的是基于真实采集证据制作的本地回放" description="回放不会访问招聘网站，不能作为新的真实采集结果；清单按附件 replay.schema.json 校验，声明变化仅用于复核，实际变化由应用解析快照后比较。" /></div>
    {scenarios.isError && <Alert type="error" message="加载回放场景失败" action={<Button onClick={() => scenarios.refetch()}>重试</Button>} />}
    {scenarios.data?.length === 0 && <Empty description="没有可用的回放清单" />}
    {scenarios.data?.map(scenario => {
      const run = results[scenario.id];
      const running = mutation.isPending && mutation.variables?.id === scenario.id;
      return <Card key={scenario.id} title={<Space><Tag color="purple">本地回放</Tag>{scenario.step_id}</Space>} extra={<Button type={scenario.kind === "source_failure" ? "default" : "primary"} danger={scenario.kind === "source_failure"} disabled={!scenario.valid} loading={running} onClick={() => mutation.mutate(scenario)}>{scenario.kind === "source_failure" ? "执行失败模拟" : "执行回放"}</Button>}>
        <Space direction="vertical" className="full-width">
          <Typography.Paragraph>{scenario.expected}</Typography.Paragraph>
          <Descriptions size="small" column={{ xs: 1, md: 2 }}>
            <Descriptions.Item label="来源">{scenario.source_code}</Descriptions.Item><Descriptions.Item label="场景类型">{scenario.kind}</Descriptions.Item>
            <Descriptions.Item label="原始证据">{scenario.provenance_file}</Descriptions.Item><Descriptions.Item label="原始 SHA-256">{scenario.provenance_sha256.slice(0, 16)}…</Descriptions.Item>
            <Descriptions.Item label="快照文件">{scenario.snapshot_file ?? "无（来源级失败）"}</Descriptions.Item><Descriptions.Item label="声明字段">{scenario.declared_fields.join("、") || "无"}</Descriptions.Item>
          </Descriptions>
          {!scenario.valid && <Alert type="error" message="场景校验失败" description={scenario.validation_error} />}
          {run && <Alert type={run.status === "success" ? "success" : "error"} showIcon message={<Space>运行结果<Tag color={statusColor(run.status)}>{run.status}</Tag><span>运行 ID：{run.id}</span></Space>} description={`有效 ${run.valid_count}，变化 ${run.changed_count}，未变化 ${run.unchanged_count}，岗位失败 ${run.failed_count}${run.error_message ? `；${run.error_message}` : ""}`} />}
        </Space>
      </Card>;
    })}
  </Space>;
}
