import axios from "axios";
import type { WatchListResponse, WatchResponse } from "../types/watches";

export async function watchJob(jobId: string) {
  const { data } = await axios.post<WatchResponse>(`/api/jobs/${jobId}/watch`);
  return data;
}

export async function unwatchJob(jobId: string) {
  await axios.delete(`/api/jobs/${jobId}/watch`);
}

export async function fetchWatches(page: number) {
  const { data } = await axios.get<WatchListResponse>("/api/watches", { params: { page, page_size: 20 } });
  return data;
}
