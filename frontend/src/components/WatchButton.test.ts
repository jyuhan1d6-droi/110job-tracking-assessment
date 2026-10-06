import { describe, expect, it } from "vitest";
import { watchButtonText } from "./WatchButton";

describe("watch button state", () => {
  it("shows active and pending labels", () => {
    expect(watchButtonText(false, false)).toBe("关注");
    expect(watchButtonText(true, false)).toBe("取消关注");
    expect(watchButtonText(false, true)).toBe("正在关注");
    expect(watchButtonText(true, true)).toBe("正在取消");
  });
});
