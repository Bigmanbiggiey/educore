import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { InviteMemberForm } from "./InviteMemberForm";

describe("InviteMemberForm", () => {
  it("blocks submission and shows a validation error when the email is empty", async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    render(<InviteMemberForm onSubmit={onSubmit} />);

    await user.click(screen.getByRole("button", { name: /invite member/i }));

    expect(await screen.findByText(/enter an email address/i)).toBeInTheDocument();
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("submits with the entered values", async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    render(<InviteMemberForm onSubmit={onSubmit} />);

    await user.type(screen.getByLabelText("Email"), "teacher@stmary.ac.ke");
    await user.selectOptions(screen.getByLabelText("Role"), "Teacher");
    await user.click(screen.getByRole("button", { name: /invite member/i }));

    await waitFor(() =>
      expect(onSubmit).toHaveBeenCalledWith(
        expect.objectContaining({
          email: "teacher@stmary.ac.ke",
          role_name: "Teacher",
        }),
        expect.anything(),
      ),
    );
  });

  it("renders a server-side error message", () => {
    render(<InviteMemberForm onSubmit={vi.fn()} errorMessage="A user with this email already exists." />);
    expect(screen.getByRole("alert")).toHaveTextContent("A user with this email already exists.");
  });

  it("disables the submit button while submitting", () => {
    render(<InviteMemberForm onSubmit={vi.fn()} isSubmitting />);
    expect(screen.getByRole("button", { name: /inviting/i })).toBeDisabled();
  });
});
