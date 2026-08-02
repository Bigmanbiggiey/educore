import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { CheckoutForm } from "./CheckoutForm";

describe("CheckoutForm", () => {
  it("blocks submission and shows validation errors when required fields are empty", async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    render(<CheckoutForm onSubmit={onSubmit} />);

    await user.click(screen.getByRole("button", { name: /check out/i }));

    expect(await screen.findByText(/enter the copy id/i)).toBeInTheDocument();
    expect(screen.getByText(/enter the borrower id/i)).toBeInTheDocument();
    expect(screen.getByText(/choose a due date/i)).toBeInTheDocument();
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("submits with the entered values", async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    render(<CheckoutForm onSubmit={onSubmit} />);

    await user.type(screen.getByLabelText("Copy ID"), "copy-1");
    await user.type(screen.getByLabelText("Borrower ID"), "borrower-1");
    await user.type(screen.getByLabelText("Due date"), "2026-08-15");
    await user.click(screen.getByRole("button", { name: /check out/i }));

    await waitFor(() =>
      expect(onSubmit).toHaveBeenCalledWith(
        expect.objectContaining({
          copy: "copy-1",
          borrower_type: "student",
          borrower_id: "borrower-1",
          due_date: "2026-08-15",
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
