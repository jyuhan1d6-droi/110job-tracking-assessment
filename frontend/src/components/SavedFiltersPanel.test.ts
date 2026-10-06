import { describe, expect, it } from "vitest";
import { buildSavedFilterParams } from "./SavedFiltersPanel";
import type { SavedFilter } from "../types/savedFilters";

const base: SavedFilter = {
  id: "filter-1", name: "方案", keyword: "AI", city: "北京",
  created_at: "2026-10-06T00:00:00Z", updated_at: "2026-10-06T00:00:00Z",
};

describe("saved filter reuse", () => {
  it("builds current-search URL params and omits empty conditions", () => {
    expect(buildSavedFilterParams(base)).toEqual({ savedFilter: "filter-1", keyword: "AI", city: "北京" });
    expect(buildSavedFilterParams({ ...base, keyword: null })).toEqual({ savedFilter: "filter-1", city: "北京" });
  });
});
