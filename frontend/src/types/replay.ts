export type ReplayScenario = {
  id: string;
  step_id: string;
  name: string;
  source_code: string;
  kind: "snapshot" | "source_failure" | "invalid";
  expected: string;
  declared_fields: string[];
  provenance_file: string;
  provenance_sha256: string;
  snapshot_file: string | null;
  snapshot_sha256: string | null;
  failure_reason: string | null;
  valid: boolean;
  validation_error: string | null;
};

export type ReplayRun = {
  id: string;
  status: string;
  started_at: string;
  finished_at: string | null;
  fetched_count: number;
  valid_count: number;
  new_count: number;
  changed_count: number;
  unchanged_count: number;
  failed_count: number;
  error_code: string | null;
  error_message: string | null;
  request_metadata: Record<string, unknown>;
};
