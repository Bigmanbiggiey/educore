import { describe, expect, it } from "vitest";

import { routeSchema } from "./route.schema";

const VALID_VEHICLE_ID = "51111111-1111-4111-8111-111111111111";

describe("routeSchema", () => {
  it("accepts a valid payload", () => {
    const result = routeSchema.safeParse({ name: "Route A", vehicle: VALID_VEHICLE_ID });
    expect(result.success).toBe(true);
  });

  it("rejects a missing name", () => {
    const result = routeSchema.safeParse({ name: "", vehicle: VALID_VEHICLE_ID });
    expect(result.success).toBe(false);
  });

  it("rejects a vehicle ID that isn't a valid UUID", () => {
    const result = routeSchema.safeParse({ name: "Route A", vehicle: "not-a-uuid" });
    expect(result.success).toBe(false);
  });
});
