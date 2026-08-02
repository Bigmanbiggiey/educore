import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { Skeleton } from "./Skeleton";

describe("Skeleton", () => {
  it("renders a single pulsing block by default", () => {
    const { container } = render(<Skeleton />);
    expect(container.querySelectorAll(".animate-pulse")).toHaveLength(1);
  });

  it("renders the requested number of stacked lines", () => {
    const { container } = render(<Skeleton lines={3} />);
    expect(container.querySelectorAll(".animate-pulse")).toHaveLength(3);
  });
});
