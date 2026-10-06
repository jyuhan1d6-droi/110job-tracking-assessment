import { describe, expect, it } from "vitest";
import { displayChangeValue } from "./ChangeValue";

describe("watch event value presentation", () => {
  it("maps missing and recruitment status values without guessing", () => {
    expect(displayChangeValue("deadline", null)).toBe("未提供");
    expect(displayChangeValue("recruitment_status", "open")).toBe("招聘中");
    expect(displayChangeValue("recruitment_status", "closed")).toBe("已关闭");
    expect(displayChangeValue("requirements", "第一行\n第二行")).toBe("第一行\n第二行");
  });
});
