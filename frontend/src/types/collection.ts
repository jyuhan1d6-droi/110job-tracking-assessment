export type CollectionRun = {
  id: string; source_code: string; source_name: string; triggered_by: string;
  status: "pending" | "running" | "success" | "partial" | "failed"; mode: "live" | "replay";
  started_at: string; finished_at: string | null;
  fetched_count: number; valid_count: number; new_count: number; changed_count: number;
  unchanged_count: number; failed_count: number; error_code: string | null;
  error_message: string | null; request_metadata: Record<string, unknown>; artifact_count: number;
};

export type CollectionSource = {
  code: string; name: string; source_type: "recruitment_platform" | "company_careers";
  entry_url: string; official_evidence_url: string | null; enabled: boolean;
  request_interval_ms: number; timeout_seconds: number; max_retries: number;
  active_run: CollectionRun | null; latest_run: CollectionRun | null; latest_success_at: string | null;
};

export type RunList = { items: CollectionRun[]; page: number; page_size: number; total: number; total_pages: number };

export type CollectionArtifact = {
  id: string; artifact_type: string; relative_path: string; request_url: string;
  content_type: string | null; http_status: number | null; byte_size: number; sha256: string;
  captured_at: string; request_headers: Record<string, unknown>; response_headers: Record<string, unknown>;
  artifact_metadata: Record<string, unknown>;
};

export type ArtifactList = { items: CollectionArtifact[]; page: number; page_size: number; total: number; total_pages: number };
