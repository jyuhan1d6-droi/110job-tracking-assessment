// @vitest-environment jsdom
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import EmptyJobsGuide from "./EmptyJobsGuide";
import { displayStatus } from "./JobCard";
import { emptyMode } from "../pages/JobsPage";

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
});
