import axios from "axios";
import type { WatchEventDetail, WatchEventListResponse } from "../types/watchEvents";

export async function fetchWatchEvents(page: number) {
  const { data } = await axios.get<WatchEventListResponse>("/api/watch-events", { params: { page, page_size: 20 } });
  return data;
}

export async function fetchWatchEvent(id: string) {
  const { data } = await axios.get<WatchEventDetail>(`/api/watch-events/${id}`);
  return data;
}
