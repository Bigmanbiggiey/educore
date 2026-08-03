import { describe, expect, it } from "vitest";

import { roomSchema } from "./room.schema";

describe("roomSchema", () => {
  it("accepts a valid payload", () => {
    const result = roomSchema.safeParse({ room_number: "A1", capacity: "4" });
    expect(result.success).toBe(true);
  });

  it("rejects a missing room number", () => {
    const result = roomSchema.safeParse({ room_number: "", capacity: "4" });
    expect(result.success).toBe(false);
  });

  it("rejects a zero capacity", () => {
    const result = roomSchema.safeParse({ room_number: "A1", capacity: "0" });
    expect(result.success).toBe(false);
  });

  it("rejects a non-numeric capacity", () => {
    const result = roomSchema.safeParse({ room_number: "A1", capacity: "many" });
    expect(result.success).toBe(false);
  });

  it("rejects a fractional capacity", () => {
    const result = roomSchema.safeParse({ room_number: "A1", capacity: "2.5" });
    expect(result.success).toBe(false);
  });
});
