import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { ProvisionInstitutionForm } from "./ProvisionInstitutionForm";

describe("ProvisionInstitutionForm", () => {
  it("blocks submission and shows validation errors when required fields are empty", async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    render(<ProvisionInstitutionForm onSubmit={onSubmit} />);

    await user.click(screen.getByRole("button", { name: /provision institution/i }));

    expect(await screen.findByText(/enter an institution name/i)).toBeInTheDocument();
    expect(screen.getByText(/enter a slug/i)).toBeInTheDocument();
    expect(screen.getByText(/enter the administrator's email/i)).toBeInTheDocument();
    expect(screen.getByText(/select at least one curriculum/i)).toBeInTheDocument();
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("submits with the entered values", async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    render(<ProvisionInstitutionForm onSubmit={onSubmit} />);

    await user.type(screen.getByLabelText("Institution name"), "St Mary");
    await user.type(screen.getByLabelText("Slug"), "st-mary");
    await user.type(screen.getByLabelText("Administrator email"), "admin@stmary.ac.ke");
    await user.click(screen.getByLabelText("CBC"));
    await user.click(screen.getByRole("button", { name: /provision institution/i }));

    await waitFor(() =>
      expect(onSubmit).toHaveBeenCalledWith(
        expect.objectContaining({
          name: "St Mary",
          slug: "st-mary",
          admin_email: "admin@stmary.ac.ke",
          curriculum_types: ["cbc"],
        }),
        expect.anything(),
      ),
    );
  });

  it("renders a server-side error message", () => {
    render(<ProvisionInstitutionForm onSubmit={vi.fn()} errorMessage="Slug already in use." />);
    expect(screen.getByRole("alert")).toHaveTextContent("Slug already in use.");
  });

  it("disables the submit button while submitting", () => {
    render(<ProvisionInstitutionForm onSubmit={vi.fn()} isSubmitting />);
    expect(screen.getByRole("button", { name: /provisioning/i })).toBeDisabled();
  });
});
