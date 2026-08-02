import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { StatTile } from "./StatTile";

describe("StatTile", () => {
  it("renders the label and value", () => {
    render(<StatTile label="Attendance rate" value="82%" />);
    expect(screen.getByText("Attendance rate")).toBeInTheDocument();
    expect(screen.getByText("82%")).toBeInTheDocument();
  });

  it("renders optional help text", () => {
    render(<StatTile label="Balance" value="KES 500" helpText="This term" />);
    expect(screen.getByText("This term")).toBeInTheDocument();
  });

  it("omits help text when not given", () => {
    render(<StatTile label="Balance" value="KES 500" />);
    expect(screen.queryByText("This term")).not.toBeInTheDocument();
  });
});
