import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { CreateStudentForm } from "./CreateStudentForm";

describe("CreateStudentForm", () => {
  it("blocks submission and shows validation errors when required fields are empty", async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    render(<CreateStudentForm onSubmit={onSubmit} />);

    await user.click(screen.getByRole("button", { name: /add student/i }));

    expect(await screen.findByText(/enter an admission number/i)).toBeInTheDocument();
    expect(screen.getByText(/enter a first name/i)).toBeInTheDocument();
    expect(screen.getByText(/enter a last name/i)).toBeInTheDocument();
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("submits with the entered values", async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    render(<CreateStudentForm onSubmit={onSubmit} />);

    await user.type(screen.getByLabelText("Admission number"), "A-100");
    await user.type(screen.getByLabelText("First name"), "Jane");
    await user.type(screen.getByLabelText("Last name"), "Doe");
    await user.click(screen.getByRole("button", { name: /add student/i }));

    await waitFor(() =>
      expect(onSubmit).toHaveBeenCalledWith(
        expect.objectContaining({
          admission_number: "A-100",
          first_name: "Jane",
          last_name: "Doe",
        }),
        expect.anything(),
      ),
    );
  });

  it("renders a server-side error message", () => {
    render(<CreateStudentForm onSubmit={vi.fn()} errorMessage="Admission number already in use." />);
    expect(screen.getByRole("alert")).toHaveTextContent("Admission number already in use.");
  });

  it("disables the submit button while submitting", () => {
    render(<CreateStudentForm onSubmit={vi.fn()} isSubmitting />);
    expect(screen.getByRole("button", { name: /adding/i })).toBeDisabled();
  });
});
