import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { RecordVisitForm } from "./RecordVisitForm";

describe("RecordVisitForm", () => {
  it("blocks submission and shows validation errors when required fields are empty", async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    render(<RecordVisitForm onSubmit={onSubmit} />);

    await user.click(screen.getByRole("button", { name: /record visit/i }));

    expect(await screen.findByText(/enter the student id/i)).toBeInTheDocument();
    expect(screen.getByText(/choose a visit date/i)).toBeInTheDocument();
    expect(screen.getByText(/enter the treating nurse's staff id/i)).toBeInTheDocument();
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("submits with the entered values", async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    render(<RecordVisitForm onSubmit={onSubmit} />);

    await user.type(screen.getByLabelText("Student ID"), "s-1");
    await user.type(screen.getByLabelText("Visit date"), "2026-08-01");
    await user.type(screen.getByLabelText("Treating nurse's staff ID"), "n-1");
    await user.click(screen.getByRole("button", { name: /record visit/i }));

    await waitFor(() =>
      expect(onSubmit).toHaveBeenCalledWith(
        expect.objectContaining({
          student_id: "s-1",
          visit_date: "2026-08-01",
          treated_by_id: "n-1",
        }),
        expect.anything(),
      ),
    );
  });

  it("renders a server-side error message", () => {
    render(<RecordVisitForm onSubmit={vi.fn()} errorMessage="Student not found." />);
    expect(screen.getByRole("alert")).toHaveTextContent("Student not found.");
  });

  it("disables the submit button while submitting", () => {
    render(<RecordVisitForm onSubmit={vi.fn()} isSubmitting />);
    expect(screen.getByRole("button", { name: /recording/i })).toBeDisabled();
  });
});
