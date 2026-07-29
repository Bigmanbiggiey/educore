import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { LoginForm } from "./LoginForm";

describe("LoginForm", () => {
  it("shows validation errors and does not submit when fields are empty", async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    render(<LoginForm onSubmit={onSubmit} />);

    await user.click(screen.getByRole("button", { name: /sign in/i }));

    expect(await screen.findByText(/enter your email or phone number/i)).toBeInTheDocument();
    expect(screen.getByText(/enter your password/i)).toBeInTheDocument();
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("calls onSubmit with the entered values", async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    render(<LoginForm onSubmit={onSubmit} />);

    await user.type(screen.getByLabelText(/email or phone/i), "teacher@stmary.ac.ke");
    await user.type(screen.getByLabelText(/password/i), "a-decent-password");
    await user.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() =>
      expect(onSubmit).toHaveBeenCalledWith(
        { emailOrPhone: "teacher@stmary.ac.ke", password: "a-decent-password" },
        expect.anything(),
      ),
    );
  });

  it("renders a server-side error message", () => {
    render(<LoginForm onSubmit={vi.fn()} errorMessage="Invalid credentials." />);

    expect(screen.getByRole("alert")).toHaveTextContent("Invalid credentials.");
  });

  it("disables the submit button while submitting", () => {
    render(<LoginForm onSubmit={vi.fn()} isSubmitting />);

    expect(screen.getByRole("button", { name: /signing in/i })).toBeDisabled();
  });
});
