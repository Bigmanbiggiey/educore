import { describe, expect, it } from "vitest";

import { formatCurrency, formatPercent } from "./format";

describe("formatPercent", () => {
  it("renders a decimal-string rate as a rounded percentage", () => {
    expect(formatPercent("0.7500")).toBe("75%");
  });

  it("renders a numeric rate as a rounded percentage", () => {
    expect(formatPercent(0.5)).toBe("50%");
  });

  it("renders null as an em dash rather than 0%", () => {
    expect(formatPercent(null)).toBe("—");
  });
});

describe("formatCurrency", () => {
  it("formats a decimal string as KES currency", () => {
    expect(formatCurrency("500.00")).toContain("500");
  });
});
