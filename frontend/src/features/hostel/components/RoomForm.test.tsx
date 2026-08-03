import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { RoomForm } from "./RoomForm";

describe("RoomForm", () => {
  it("blocks submission and shows validation errors when required fields are empty", async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    render(<RoomForm onSubmit={onSubmit} />);

    await user.click(screen.getByRole("button", { name: /save changes/i }));

    expect(await screen.findByText(/enter a room number/i)).toBeInTheDocument();
    expect(screen.getByText(/enter a capacity/i)).toBeInTheDocument();
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("submits with the entered values", async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    render(<RoomForm onSubmit={onSubmit} />);

    await user.type(screen.getByLabelText("Room number"), "A1");
    await user.type(screen.getByLabelText("Capacity"), "4");
    await user.click(screen.getByRole("button", { name: /save changes/i }));

    await waitFor(() =>
      expect(onSubmit).toHaveBeenCalledWith(
        expect.objectContaining({ room_number: "A1", capacity: "4" }),
        expect.anything(),
      ),
    );
  });

  it("prefills fields from defaultValues", () => {
    render(<RoomForm onSubmit={vi.fn()} defaultValues={{ room_number: "A1", capacity: "4" }} />);
    expect(screen.getByLabelText("Room number")).toHaveValue("A1");
    expect(screen.getByLabelText("Capacity")).toHaveValue(4);
  });

  it("renders a server-side error message", () => {
    render(<RoomForm onSubmit={vi.fn()} errorMessage="Room number already in use." />);
    expect(screen.getByRole("alert")).toHaveTextContent("Room number already in use.");
  });

  it("disables the submit button while submitting", () => {
    render(<RoomForm onSubmit={vi.fn()} isSubmitting />);
    expect(screen.getByRole("button", { name: /saving/i })).toBeDisabled();
  });
});
