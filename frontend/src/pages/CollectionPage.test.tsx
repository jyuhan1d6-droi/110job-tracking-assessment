// @vitest-environment jsdom
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeAll, beforeEach, describe, expect, it, vi } from "vitest";
import CollectionPage from "./CollectionPage";

const fetchSources = vi.fn();
const fetchRuns = vi.fn();
const start = vi.fn();
const fetchRun = vi.fn();
const fetchArtifacts = vi.fn();

vi.mock("../api/collection", () => ({
  fetchCollectionSources: () => fetchSources(),
  fetchCollectionRuns: () => fetchRuns(),
  startCollection: (code: string) => start(code),
  fetchCollectionRun: () => fetchRun(),
  fetchRunArtifacts: () => fetchArtifacts(),
}));

beforeAll(() => {
  Object.defineProperty(window, "matchMedia", { writable: true, value: vi.fn().mockImplementation(query => ({
    matches: false, media: query, onchange: null, addListener: vi.fn(), removeListener: vi.fn(),
    addEventListener: vi.fn(), removeEventListener: vi.fn(), dispatchEvent: vi.fn(),
  })) });
});

beforeEach(() => {
  vi.clearAllMocks();
  fetchSources.mockResolvedValue([{
    code: "360-careers", name: "360 招聘", source_type: "company_careers",
    entry_url: "https://hr.360.cn/hr/list", official_evidence_url: "https://hr.360.cn/hr/",
    enabled: true, request_interval_ms: 1000, timeout_seconds: 15, max_retries: 2,
    active_run: null, latest_run: null, latest_success_at: null,
  }]);
  fetchRuns.mockResolvedValue({ items: [], page: 1, page_size: 20, total: 0, total_pages: 0 });
  start.mockResolvedValue({
    id: "run-1", source_code: "360-careers", source_name: "360 招聘", triggered_by: "维护员",
    status: "pending", mode: "live", started_at: "2026-10-06T00:00:00Z", finished_at: null,
    fetched_count: 0, valid_count: 0, new_count: 0, changed_count: 0, unchanged_count: 0,
    failed_count: 0, error_code: null, error_message: null, request_metadata: {}, artifact_count: 0,
  });
  fetchRun.mockResolvedValue({
    id: "run-1", source_code: "360-careers", source_name: "360 招聘", triggered_by: "维护员",
    status: "pending", mode: "live", started_at: "2026-10-06T00:00:00Z", finished_at: null,
    fetched_count: 0, valid_count: 0, new_count: 0, changed_count: 0, unchanged_count: 0,
    failed_count: 0, error_code: null, error_message: null, request_metadata: {}, artifact_count: 0,
  });
  fetchArtifacts.mockResolvedValue({ items: [], page: 1, page_size: 50, total: 0, total_pages: 0 });
});

describe("maintainer collection page", () => {
  it("loads fixed sources and starts a real collection through the normal API", async () => {
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(<QueryClientProvider client={client}><CollectionPage /></QueryClientProvider>);
    expect(await screen.findByText("360 招聘")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "开始真实采集" }));
    await waitFor(() => expect(start).toHaveBeenCalledWith("360-careers"));
  });
});
