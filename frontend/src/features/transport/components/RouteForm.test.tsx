import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { RouteForm } from "./RouteForm";

const VALID_VEHICLE_ID = "51111111-1111-4111-8111-111111111111";

describe("RouteForm", () => {
  it("blocks submission and shows validation errors when required fields are empty", async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    render(<RouteForm onSubmit={onSubmit} />);

    await user.click(screen.getByRole("button", { name: /save changes/i }));

    expect(await screen.findByText(/enter a route name/i)).toBeInTheDocument();
    expect(screen.getByText(/enter a valid vehicle id/i)).toBeInTheDocument();
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("submits with the entered values", async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    render(<RouteForm onSubmit={onSubmit} />);

    await user.type(screen.getByLabelText("Route name"), "Route A");
    await user.type(screen.getByLabelText("Vehicle ID"), VALID_VEHICLE_ID);
    await user.click(screen.getByRole("button", { name: /save changes/i }));

    await waitFor(() =>
      expect(onSubmit).toHaveBeenCalledWith(
        expect.objectContaining({ name: "Route A", vehicle: VALID_VEHICLE_ID }),
        expect.anything(),
      ),
    );
  });

  it("prefills fields from defaultValues", () => {
    render(
      <RouteForm onSubmit={vi.fn()} defaultValues={{ name: "Route A", vehicle: VALID_VEHICLE_ID }} />,
    );
    expect(screen.getByLabelText("Route name")).toHaveValue("Route A");
    expect(screen.getByLabelText("Vehicle ID")).toHaveValue(VALID_VEHICLE_ID);
  });

  it("renders a server-side error message", () => {
    render(<RouteForm onSubmit={vi.fn()} errorMessage="Vehicle not found." />);
    expect(screen.getByRole("alert")).toHaveTextContent("Vehicle not found.");
  });

  it("disables the submit button while submitting", () => {
    render(<RouteForm onSubmit={vi.fn()} isSubmitting />);
    expect(screen.getByRole("button", { name: /saving/i })).toBeDisabled();
  });
});
