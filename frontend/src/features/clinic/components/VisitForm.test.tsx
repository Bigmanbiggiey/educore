import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { VisitForm } from "./VisitForm";

function isoDate(daysFromToday: number): string {
  const date = new Date();
  date.setDate(date.getDate() + daysFromToday);
  return date.toISOString().slice(0, 10);
}

const VALID_STUDENT_ID = "51111111-1111-4111-8111-111111111111";
const VALID_STAFF_ID = "c1111111-1111-4111-8111-111111111111";

describe("VisitForm", () => {
  it("blocks submission and shows validation errors when required fields are empty", async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    render(<VisitForm onSubmit={onSubmit} />);

    await user.click(screen.getByRole("button", { name: /record visit/i }));

    expect(await screen.findByText(/enter a valid student id/i)).toBeInTheDocument();
    expect(screen.getByText(/choose a visit date/i)).toBeInTheDocument();
    expect(screen.getByText(/enter a valid staff id/i)).toBeInTheDocument();
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("submits with the entered values", async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    render(<VisitForm onSubmit={onSubmit} />);

    const visitDate = isoDate(0);
    await user.type(screen.getByLabelText("Student ID"), VALID_STUDENT_ID);
    await user.type(screen.getByLabelText("Visit date"), visitDate);
    await user.type(screen.getByLabelText("Treating nurse's staff ID"), VALID_STAFF_ID);
    await user.click(screen.getByRole("button", { name: /record visit/i }));

    await waitFor(() =>
      expect(onSubmit).toHaveBeenCalledWith(
        expect.objectContaining({
          student_id: VALID_STUDENT_ID,
          visit_date: visitDate,
          treated_by_id: VALID_STAFF_ID,
        }),
        expect.anything(),
      ),
    );
  });

  it("renders a server-side error message", () => {
    render(<VisitForm onSubmit={vi.fn()} errorMessage="Student not found." />);
    expect(screen.getByRole("alert")).toHaveTextContent("Student not found.");
  });

  it("disables the submit button while submitting", () => {
    render(<VisitForm onSubmit={vi.fn()} isSubmitting />);
    expect(screen.getByRole("button", { name: /recording/i })).toBeDisabled();
  });

  it("prefills fields from defaultValues and supports a custom submit label", () => {
    render(
      <VisitForm
        onSubmit={vi.fn()}
        defaultValues={{ student_id: VALID_STUDENT_ID, notes: "Follow-up" }}
        submitLabel="Save changes"
      />,
    );
    expect(screen.getByLabelText("Student ID")).toHaveValue(VALID_STUDENT_ID);
    expect(screen.getByLabelText("Notes")).toHaveValue("Follow-up");
    expect(screen.getByRole("button", { name: "Save changes" })).toBeInTheDocument();
  });
});
