import { describe, expect, it } from "vitest";

import { resetPasswordSchema } from "./reset-password.schema";

describe("resetPasswordSchema", () => {
  it("accepts matching passwords of sufficient length", () => {
    const result = resetPasswordSchema.safeParse({
      newPassword: "a-decent-password",
      confirmPassword: "a-decent-password",
    });
    expect(result.success).toBe(true);
  });

  it("rejects a password shorter than 10 characters", () => {
    const result = resetPasswordSchema.safeParse({
      newPassword: "short",
      confirmPassword: "short",
    });
    expect(result.success).toBe(false);
  });

  it("rejects mismatched passwords and flags confirmPassword", () => {
    const result = resetPasswordSchema.safeParse({
      newPassword: "a-decent-password",
      confirmPassword: "a-different-password",
    });
    expect(result.success).toBe(false);
    if (!result.success) {
      expect(result.error.issues[0].path).toEqual(["confirmPassword"]);
    }
  });
});
