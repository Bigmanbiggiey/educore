import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { Select } from "./Select";

const options = [
  { value: "cash", label: "Cash" },
  { value: "bank", label: "Bank" },
];

describe("Select", () => {
  it("renders the label and all options", () => {
    render(<Select label="Method" name="method" options={options} onChange={() => {}} />);
    expect(screen.getByLabelText("Method")).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "Cash" })).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "Bank" })).toBeInTheDocument();
  });

  it("renders an error message and marks the field invalid", () => {
    render(
      <Select label="Method" name="method" options={options} error="Required" onChange={() => {}} />,
    );
    expect(screen.getByRole("alert")).toHaveTextContent("Required");
    expect(screen.getByLabelText("Method")).toHaveAttribute("aria-invalid", "true");
  });

  it("calls onChange when a new option is selected", async () => {
    const user = userEvent.setup();
    let selected = "";
    render(
      <Select
        label="Method"
        name="method"
        options={options}
        onChange={(event) => {
          selected = event.target.value;
        }}
      />,
    );

    await user.selectOptions(screen.getByLabelText("Method"), "bank");
    expect(selected).toBe("bank");
  });
});
