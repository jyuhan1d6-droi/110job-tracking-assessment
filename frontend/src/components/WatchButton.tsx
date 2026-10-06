import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Button, message } from "antd";
import { unwatchJob, watchJob } from "../api/watches";

export function watchButtonText(isWatched: boolean, isPending: boolean) {
  if (isPending) return isWatched ? "正在取消" : "正在关注";
  return isWatched ? "取消关注" : "关注";
}

export default function WatchButton({ jobId, isWatched }: { jobId: string; isWatched: boolean }) {
  const queryClient = useQueryClient();
  const mutation = useMutation({
    mutationFn: async () => {
      if (isWatched) await unwatchJob(jobId);
      else await watchJob(jobId);
    },
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["jobs"] }),
        queryClient.invalidateQueries({ queryKey: ["job", jobId] }),
        queryClient.invalidateQueries({ queryKey: ["watches"] }),
      ]);
      message.success(isWatched ? "已取消关注，历史关注区间仍保留" : "已关注岗位");
    },
    onError: () => message.error(isWatched ? "取消关注失败，请重试" : "关注失败，请重试"),
  });
  return <Button danger={isWatched} loading={mutation.isPending} onClick={() => mutation.mutate()}>
    {watchButtonText(isWatched, mutation.isPending)}
  </Button>;
}
