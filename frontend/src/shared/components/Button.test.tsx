import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { Button } from "./Button";

describe("Button", () => {
  it("renders children and defaults to the primary variant", () => {
    render(<Button>Save</Button>);
    const button = screen.getByRole("button", { name: "Save" });
    expect(button).toHaveClass("bg-primary");
  });

  it.each(["primary", "secondary", "outline", "ghost", "danger"] as const)(
    "renders the %s variant without crashing",
    (variant) => {
      render(<Button variant={variant}>Action</Button>);
      expect(screen.getByRole("button", { name: "Action" })).toBeInTheDocument();
    },
  );

  it("merges a caller-supplied className instead of duplicating conflicting utilities", () => {
    render(<Button className="px-8">Wide</Button>);
    const button = screen.getByRole("button", { name: "Wide" });
    expect(button).toHaveClass("px-8");
    expect(button.className).not.toMatch(/px-4/);
  });

  it("is disabled when the disabled prop is passed", () => {
    render(<Button disabled>Locked</Button>);
    expect(screen.getByRole("button", { name: "Locked" })).toBeDisabled();
  });
});
