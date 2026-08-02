import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { QueryBoundary } from "./QueryBoundary";

describe("QueryBoundary", () => {
  it("renders a loading skeleton while pending", () => {
    const { container } = render(
      <QueryBoundary query={{ isPending: true, isError: false, error: null, data: undefined }}>
        {() => <p>Loaded</p>}
      </QueryBoundary>,
    );
    expect(container.querySelector(".animate-pulse")).toBeInTheDocument();
  });

  it("renders the default error message on failure", () => {
    render(
      <QueryBoundary
        query={{ isPending: false, isError: true, error: new Error("Network down"), data: undefined }}
      >
        {() => <p>Loaded</p>}
      </QueryBoundary>,
    );
    expect(screen.getByRole("alert")).toHaveTextContent("Network down");
  });

  it("renders a custom error fallback when given", () => {
    render(
      <QueryBoundary
        query={{ isPending: false, isError: true, error: new Error("x"), data: undefined }}
        errorFallback={() => <p>Custom error</p>}
      >
        {() => <p>Loaded</p>}
      </QueryBoundary>,
    );
    expect(screen.getByText("Custom error")).toBeInTheDocument();
  });

  it("renders children with data on success", () => {
    render(
      <QueryBoundary query={{ isPending: false, isError: false, error: null, data: { name: "Jane" } }}>
        {(data) => <p>{data.name}</p>}
      </QueryBoundary>,
    );
    expect(screen.getByText("Jane")).toBeInTheDocument();
  });
});
