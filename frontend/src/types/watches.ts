import type { JobListItem } from "./jobs";

export type WatchResponse = {
  id: string;
  job_id: string;
  watched_at: string;
  is_active: boolean;
};

export type WatchedJobItem = {
  watch_id: string;
  watched_at: string;
  job: JobListItem;
};

export type WatchListResponse = {
  items: WatchedJobItem[];
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
};
