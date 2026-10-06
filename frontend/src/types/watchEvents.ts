import type { SourceBrief } from "./jobs";

export type ChangedField = {
  field_name: "requirements" | "deadline" | "recruitment_status";
  before_text: string | null;
  after_text: string | null;
};

export type WatchEventListItem = {
  id: string;
  watch_id: string;
  watched_at: string;
  job_id: string;
  title: string;
  company: string;
  city: string;
  recruitment_status: "open" | "closed" | null;
  status_provided: boolean;
  detected_at: string;
  origin: "live" | "replay";
  changed_fields: ChangedField["field_name"][];
  change_count: number;
  source: SourceBrief;
};

export type WatchEventListResponse = {
  items: WatchEventListItem[];
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
};

export type WatchEventDetail = WatchEventListItem & {
  detail_url: string;
  changes: ChangedField[];
};
