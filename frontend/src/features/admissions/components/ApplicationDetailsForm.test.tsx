import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { ApplicationDetailsForm } from "./ApplicationDetailsForm";

const VALID_TERM_ID = "51111111-1111-4111-8111-111111111111";

describe("ApplicationDetailsForm", () => {
  it("blocks submission and shows validation errors when required fields are empty", async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    render(<ApplicationDetailsForm onSubmit={onSubmit} />);

    await user.click(screen.getByRole("button", { name: /save changes/i }));

    expect(await screen.findByText(/enter a first name/i)).toBeInTheDocument();
    expect(screen.getByText(/enter a last name/i)).toBeInTheDocument();
    expect(screen.getByText(/enter a valid term id/i)).toBeInTheDocument();
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("submits with the entered values", async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    render(<ApplicationDetailsForm onSubmit={onSubmit} />);

    await user.type(screen.getByLabelText("First name"), "Jane");
    await user.type(screen.getByLabelText("Last name"), "Doe");
    await user.type(screen.getByLabelText("Term applying for ID"), VALID_TERM_ID);
    await user.click(screen.getByRole("button", { name: /save changes/i }));

    await waitFor(() =>
      expect(onSubmit).toHaveBeenCalledWith(
        expect.objectContaining({
          first_name: "Jane",
          last_name: "Doe",
          term_applying_for_id: VALID_TERM_ID,
        }),
        expect.anything(),
      ),
    );
  });

  it("prefills fields from defaultValues", () => {
    render(
      <ApplicationDetailsForm
        onSubmit={vi.fn()}
        defaultValues={{ first_name: "Jane", last_name: "Doe" }}
      />,
    );
    expect(screen.getByLabelText("First name")).toHaveValue("Jane");
    expect(screen.getByLabelText("Last name")).toHaveValue("Doe");
  });

  it("renders a server-side error message", () => {
    render(<ApplicationDetailsForm onSubmit={vi.fn()} errorMessage="Term not found." />);
    expect(screen.getByRole("alert")).toHaveTextContent("Term not found.");
  });

  it("disables the submit button while submitting", () => {
    render(<ApplicationDetailsForm onSubmit={vi.fn()} isSubmitting />);
    expect(screen.getByRole("button", { name: /saving/i })).toBeDisabled();
  });
});
