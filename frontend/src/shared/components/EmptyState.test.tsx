import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { EmptyState } from "./EmptyState";

describe("EmptyState", () => {
  it("renders the message", () => {
    render(<EmptyState message="No students yet." />);
    expect(screen.getByText("No students yet.")).toBeInTheDocument();
  });

  it("renders an optional action", () => {
    render(<EmptyState message="No students yet." action={<button>Add student</button>} />);
    expect(screen.getByRole("button", { name: "Add student" })).toBeInTheDocument();
  });
});
