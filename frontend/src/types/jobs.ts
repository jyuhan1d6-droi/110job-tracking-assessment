export type CurrentUser = {
  id: string;
  username: string;
  display_name: string;
  role: "job_seeker" | "maintainer";
};

export type SourceBrief = {
  code: string;
  name: string;
  source_type: "recruitment_platform" | "company_careers";
  entry_url: string;
};

export type JobListItem = {
  id: string;
  title: string;
  company: string;
  city: string;
  requirements_summary: string;
  deadline_raw: string | null;
  deadline_provided: boolean;
  recruitment_status: "open" | "closed" | null;
  status_provided: boolean;
  detail_url: string;
  last_seen_at: string;
  source: SourceBrief;
  is_watched: boolean;
};

export type JobDetail = Omit<JobListItem, "requirements_summary"> & {
  external_identity: string;
  requirements: string;
  deadline_at: string | null;
  first_seen_at: string;
  last_changed_at: string | null;
};

export type JobListResponse = {
  items: JobListItem[];
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
  filters: { keyword: string; city: string };
};

export type JobSummary = {
  total_visible_jobs: number;
  sources_with_jobs: number;
  last_collected_at: string | null;
};
