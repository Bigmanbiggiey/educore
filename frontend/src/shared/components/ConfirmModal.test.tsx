import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { ConfirmModal } from "./ConfirmModal";

describe("ConfirmModal", () => {
  it("renders nothing when closed", () => {
    render(
      <ConfirmModal
        open={false}
        title="Delete student"
        message="Are you sure?"
        onConfirm={vi.fn()}
        onCancel={vi.fn()}
      />,
    );
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("renders the title and message when open", () => {
    render(
      <ConfirmModal
        open
        title="Delete student"
        message="This cannot be undone."
        onConfirm={vi.fn()}
        onCancel={vi.fn()}
      />,
    );
    expect(screen.getByRole("dialog")).toBeInTheDocument();
    expect(screen.getByText("This cannot be undone.")).toBeInTheDocument();
  });

  it("calls onConfirm when the confirm button is clicked", async () => {
    const onConfirm = vi.fn();
    const user = userEvent.setup();
    render(
      <ConfirmModal
        open
        title="Delete student"
        message="Are you sure?"
        onConfirm={onConfirm}
        onCancel={vi.fn()}
      />,
    );

    await user.click(screen.getByRole("button", { name: "Delete" }));
    expect(onConfirm).toHaveBeenCalled();
  });

  it("calls onCancel when the cancel button is clicked", async () => {
    const onCancel = vi.fn();
    const user = userEvent.setup();
    render(
      <ConfirmModal
        open
        title="Delete student"
        message="Are you sure?"
        onConfirm={vi.fn()}
        onCancel={onCancel}
      />,
    );

    await user.click(screen.getByRole("button", { name: "Cancel" }));
    expect(onCancel).toHaveBeenCalled();
  });

  it("disables both buttons and shows a busy label while confirming", () => {
    render(
      <ConfirmModal
        open
        title="Delete student"
        message="Are you sure?"
        onConfirm={vi.fn()}
        onCancel={vi.fn()}
        isConfirming
      />,
    );
    expect(screen.getByRole("button", { name: "Deleting…" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Cancel" })).toBeDisabled();
  });

  it("supports a custom confirm label", () => {
    render(
      <ConfirmModal
        open
        title="Remove allocation"
        message="Free this bed?"
        onConfirm={vi.fn()}
        onCancel={vi.fn()}
        confirmLabel="Remove"
      />,
    );
    expect(screen.getByRole("button", { name: "Remove" })).toBeInTheDocument();
  });
});
