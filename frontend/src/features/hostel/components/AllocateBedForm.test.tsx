import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { AllocateBedForm } from "./AllocateBedForm";

describe("AllocateBedForm", () => {
  it("blocks submission when the student ID is empty", async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    render(<AllocateBedForm onSubmit={onSubmit} />);

    await user.click(screen.getByRole("button", { name: /allocate bed/i }));

    expect(await screen.findByText(/enter the student id/i)).toBeInTheDocument();
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("submits with the entered student ID", async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    render(<AllocateBedForm onSubmit={onSubmit} />);

    await user.type(screen.getByLabelText("Student ID"), "s-1");
    await user.click(screen.getByRole("button", { name: /allocate bed/i }));

    await waitFor(() =>
      expect(onSubmit).toHaveBeenCalledWith(
        expect.objectContaining({ student_id: "s-1" }),
        expect.anything(),
      ),
    );
  });

  it("renders a server-side error message", () => {
    render(<AllocateBedForm onSubmit={vi.fn()} errorMessage="This room is full." />);
    expect(screen.getByRole("alert")).toHaveTextContent("This room is full.");
  });

  it("disables the submit button while submitting", () => {
    render(<AllocateBedForm onSubmit={vi.fn()} isSubmitting />);
    expect(screen.getByRole("button", { name: /allocating/i })).toBeDisabled();
  });
});
