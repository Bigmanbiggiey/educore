import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { Card } from "./Card";

describe("Card", () => {
  it("renders its children inside a rounded surface", () => {
    render(<Card>Content</Card>);
    expect(screen.getByText("Content")).toBeInTheDocument();
  });

  it("merges a caller-supplied className", () => {
    render(<Card data-testid="card" className="p-2" />);
    const card = screen.getByTestId("card");
    expect(card).toHaveClass("p-2");
    expect(card.className).not.toMatch(/\bp-6\b/);
  });
});
