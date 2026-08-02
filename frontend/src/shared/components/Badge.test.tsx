import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { Badge } from "./Badge";

describe("Badge", () => {
  it("renders its label", () => {
    render(<Badge>Active</Badge>);
    expect(screen.getByText("Active")).toBeInTheDocument();
  });

  it.each(["neutral", "success", "warning", "danger"] as const)(
    "renders the %s tone without crashing",
    (tone) => {
      render(<Badge tone={tone}>Status</Badge>);
      expect(screen.getByText("Status")).toBeInTheDocument();
    },
  );
});
