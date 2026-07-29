import { describe, expect, it } from "vitest";

import { portalSlugsForRoles } from "./portal-routing";

describe("portalSlugsForRoles", () => {
  it("maps a single role to its portal", () => {
    expect(portalSlugsForRoles(["Teacher"])).toEqual(["teacher"]);
  });

  it("de-duplicates Principal and Deputy Principal to one portal", () => {
    expect(portalSlugsForRoles(["Principal", "Deputy Principal"])).toEqual(["principal"]);
  });

  it("returns multiple distinct portals for multiple roles", () => {
    expect(portalSlugsForRoles(["Teacher", "Principal"]).sort()).toEqual([
      "principal",
      "teacher",
    ]);
  });

  it("ignores roles with no mapped portal (e.g. System Administrator)", () => {
    expect(portalSlugsForRoles(["System Administrator"])).toEqual([]);
  });

  it("returns an empty list for no roles", () => {
    expect(portalSlugsForRoles([])).toEqual([]);
  });
});
