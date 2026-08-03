import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { CheckoutForm } from "./CheckoutForm";

function isoDate(daysFromToday: number): string {
  const date = new Date();
  date.setDate(date.getDate() + daysFromToday);
  return date.toISOString().slice(0, 10);
}

const VALID_COPY_ID = "c1111111-1111-4111-8111-111111111111";
const VALID_BORROWER_ID = "51111111-1111-4111-8111-111111111111";

describe("CheckoutForm", () => {
  it("blocks submission and shows validation errors when required fields are empty", async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    render(<CheckoutForm onSubmit={onSubmit} />);

    await user.click(screen.getByRole("button", { name: /check out/i }));

    expect(await screen.findByText(/enter a valid copy id/i)).toBeInTheDocument();
    expect(screen.getByText(/enter a valid borrower id/i)).toBeInTheDocument();
    expect(screen.getByText(/choose a due date/i)).toBeInTheDocument();
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("rejects a copy ID that isn't a valid UUID", async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    render(<CheckoutForm onSubmit={onSubmit} />);

    await user.type(screen.getByLabelText("Copy ID"), "not-a-uuid");
    await user.type(screen.getByLabelText("Borrower ID"), VALID_BORROWER_ID);
    await user.type(screen.getByLabelText("Due date"), isoDate(14));
    await user.click(screen.getByRole("button", { name: /check out/i }));

    expect(await screen.findByText(/enter a valid copy id/i)).toBeInTheDocument();
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("submits with the entered values", async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    render(<CheckoutForm onSubmit={onSubmit} />);

    const dueDate = isoDate(14);
    await user.type(screen.getByLabelText("Copy ID"), VALID_COPY_ID);
    await user.type(screen.getByLabelText("Borrower ID"), VALID_BORROWER_ID);
    await user.type(screen.getByLabelText("Due date"), dueDate);
    await user.click(screen.getByRole("button", { name: /check out/i }));

    await waitFor(() =>
      expect(onSubmit).toHaveBeenCalledWith(
        expect.objectContaining({
          copy: VALID_COPY_ID,
          borrower_type: "student",
          borrower_id: VALID_BORROWER_ID,
          due_date: dueDate,
        }),
        expect.anything(),
      ),
    );
  });

  it("renders a server-side error message", () => {
    render(<CheckoutForm onSubmit={vi.fn()} errorMessage="This copy is not available." />);
    expect(screen.getByRole("alert")).toHaveTextContent("This copy is not available.");
  });

  it("disables the submit button while submitting", () => {
    render(<CheckoutForm onSubmit={vi.fn()} isSubmitting />);
    expect(screen.getByRole("button", { name: /checking out/i })).toBeDisabled();
  });
});
