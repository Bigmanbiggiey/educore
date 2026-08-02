import { describe, expect, it } from "vitest";

import { applicantName, canMakeOffer } from "./types";
import type { Application } from "./types";

function makeApplication(overrides: Partial<Application>): Application {
  return {
    id: "a-1",
    stage: "submitted",
    stage_history: [],
    offers: [],
    term_applying_for_id: "t-1",
    created_at: "2026-08-01T00:00:00Z",
    updated_at: "2026-08-01T00:00:00Z",
    ...overrides,
  };
}

describe("canMakeOffer", () => {
  it("is eligible when submitted", () => {
    expect(canMakeOffer(makeApplication({ stage: "submitted" }))).toBe(true);
  });

  it("is eligible when under review", () => {
    expect(canMakeOffer(makeApplication({ stage: "under_review" }))).toBe(true);
  });

  it("is not eligible once already offered", () => {
    expect(canMakeOffer(makeApplication({ stage: "offered" }))).toBe(false);
  });
});

describe("applicantName", () => {
  it("reads a `name` field", () => {
    const application = makeApplication({ applicant_details: { name: "Jane Doe" } });
    expect(applicantName(application)).toBe("Jane Doe");
  });

  it("joins first/last name fields", () => {
    const application = makeApplication({
      applicant_details: { first_name: "Jane", last_name: "Doe" },
    });
    expect(applicantName(application)).toBe("Jane Doe");
  });

  it("falls back when details are missing", () => {
    expect(applicantName(makeApplication({ applicant_details: undefined }))).toBe(
      "Unnamed applicant",
    );
  });
});
