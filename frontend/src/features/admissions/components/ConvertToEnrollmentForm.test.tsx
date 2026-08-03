import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { ConvertToEnrollmentForm } from "./ConvertToEnrollmentForm";

const VALID_CLASS_GRADE_ID = "c1111111-1111-4111-8111-111111111111";
const VALID_TERM_ID = "51111111-1111-4111-8111-111111111111";

describe("ConvertToEnrollmentForm", () => {
  it("blocks submission and shows validation errors when required fields are empty", async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    render(<ConvertToEnrollmentForm onSubmit={onSubmit} />);

    await user.click(screen.getByRole("button", { name: /convert to enrollment/i }));

    expect(await screen.findByText(/enter an admission number/i)).toBeInTheDocument();
    expect(screen.getByText(/enter a valid class grade id/i)).toBeInTheDocument();
    expect(screen.getByText(/enter a valid term id/i)).toBeInTheDocument();
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("submits with the entered values, leaving stream ID out when blank", async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    render(<ConvertToEnrollmentForm onSubmit={onSubmit} />);

    await user.type(screen.getByLabelText("Admission number"), "A-100");
    await user.type(screen.getByLabelText("Class grade ID"), VALID_CLASS_GRADE_ID);
    await user.type(screen.getByLabelText("Term ID"), VALID_TERM_ID);
    await user.click(screen.getByRole("button", { name: /convert to enrollment/i }));

    await waitFor(() =>
      expect(onSubmit).toHaveBeenCalledWith(
        expect.objectContaining({
          admission_number: "A-100",
          class_grade_id: VALID_CLASS_GRADE_ID,
          term_id: VALID_TERM_ID,
          stream_id: undefined,
        }),
        expect.anything(),
      ),
    );
  });

  it("renders a server-side error message", () => {
    render(<ConvertToEnrollmentForm onSubmit={vi.fn()} errorMessage="Class grade not found." />);
    expect(screen.getByRole("alert")).toHaveTextContent("Class grade not found.");
  });

  it("disables the submit button while submitting", () => {
    render(<ConvertToEnrollmentForm onSubmit={vi.fn()} isSubmitting />);
    expect(screen.getByRole("button", { name: /converting/i })).toBeDisabled();
  });
});
