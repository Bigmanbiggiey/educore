import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { RecordPaymentForm } from "./RecordPaymentForm";

describe("RecordPaymentForm", () => {
  it("blocks submission when the amount is empty", async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    render(<RecordPaymentForm onSubmit={onSubmit} />);

    await user.click(screen.getByRole("button", { name: /record payment/i }));

    expect(await screen.findByText(/enter an amount/i)).toBeInTheDocument();
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("submits with the entered values", async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    render(<RecordPaymentForm onSubmit={onSubmit} />);

    await user.type(screen.getByLabelText("Amount"), "500");
    await user.type(screen.getByLabelText("Paid at"), "2026-01-10T09:00");
    await user.click(screen.getByRole("button", { name: /record payment/i }));

    await waitFor(() =>
      expect(onSubmit).toHaveBeenCalledWith(
        expect.objectContaining({ amount: "500", method: "cash" }),
        expect.anything(),
      ),
    );
  });

  it("renders a server-side error message", () => {
    render(<RecordPaymentForm onSubmit={vi.fn()} errorMessage="This invoice is already paid." />);
    expect(screen.getByRole("alert")).toHaveTextContent("This invoice is already paid.");
  });
});
