// @vitest-environment jsdom
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { beforeAll, describe, expect, it, vi } from "vitest";
import EmptyJobsGuide from "./EmptyJobsGuide";
import JobCard, { displayStatus } from "./JobCard";
import { emptyMode } from "../pages/JobsPage";

beforeAll(() => {
  Object.defineProperty(window, "matchMedia", {
    writable: true,
    value: vi.fn().mockImplementation(query => ({
      matches: false, media: query, onchange: null,
      addListener: vi.fn(), removeListener: vi.fn(),
      addEventListener: vi.fn(), removeEventListener: vi.fn(), dispatchEvent: vi.fn(),
    })),
  });
});

describe("job presentation", () => {
  it("does not guess a missing recruitment status", () => {
    expect(displayStatus({ status_provided: false, recruitment_status: null })).toBe("未提供");
    expect(displayStatus({ status_provided: true, recruitment_status: "open" })).toBe("招聘中");
    expect(displayStatus({ status_provided: true, recruitment_status: "closed" })).toBe("已关闭");
  });

  it("shows different first-use guidance by role", () => {
    const { rerender } = render(<MemoryRouter><EmptyJobsGuide user={{ id: "1", username: "a", display_name: "A", role: "job_seeker" }} /></MemoryRouter>);
    expect(screen.getByText("请联系数据维护账号完成首次采集。")).toBeTruthy();
    rerender(<MemoryRouter><EmptyJobsGuide user={{ id: "2", username: "m", display_name: "M", role: "maintainer" }} /></MemoryRouter>);
    expect(screen.getByText("请先使用数据维护功能采集实习僧和 360 招聘岗位。")).toBeTruthy();
  });

  it("distinguishes first use from an empty filter result", () => {
    expect(emptyMode(0, 0)).toBe("first-use");
    expect(emptyMode(35, 0)).toBe("filtered-empty");
    expect(emptyMode(35, 8)).toBe("results");
  });

  it("shows live collection and replay processing times separately", () => {
    const queryClient = new QueryClient();
    render(<QueryClientProvider client={queryClient}><MemoryRouter><JobCard job={{
      id: "job-1", title: "岗位", company: "公司", city: "北京", requirements_summary: "要求",
      deadline_raw: null, deadline_provided: false, recruitment_status: null,
      status_provided: false, detail_url: "https://example.test/job", last_seen_at: "2026-10-06T03:00:00Z",
      last_live_seen_at: "2026-10-05T03:00:00Z", last_replay_seen_at: "2026-10-06T03:00:00Z",
      last_update_mode: "replay", source: { code: "test", name: "来源", source_type: "recruitment_platform", entry_url: "https://example.test" },
      is_watched: false,
    }} /></MemoryRouter></QueryClientProvider>);
    expect(screen.getByText("最近真实采集")).toBeTruthy();
    expect(screen.getByText("最近回放处理")).toBeTruthy();
    expect(screen.queryByText("最近抓取")).toBeNull();
  });
});
