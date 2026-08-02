import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { Table } from "./Table";

interface Row {
  id: string;
  name: string;
}

const columns = [{ key: "name", header: "Name", render: (row: Row) => row.name }];

describe("Table", () => {
  it("renders a row per item using the provided columns", () => {
    const rows: Row[] = [
      { id: "1", name: "Jane" },
      { id: "2", name: "Kim" },
    ];
    render(<Table columns={columns} rows={rows} getRowKey={(row) => row.id} />);

    expect(screen.getByText("Jane")).toBeInTheDocument();
    expect(screen.getByText("Kim")).toBeInTheDocument();
  });

  it("renders an empty state when there are no rows", () => {
    render(<Table columns={columns} rows={[]} getRowKey={(row) => row.id} emptyMessage="No rows." />);
    expect(screen.getByText("No rows.")).toBeInTheDocument();
  });

  it("renders pagination controls and calls onPageChange", async () => {
    const user = userEvent.setup();
    const onPageChange = vi.fn();
    const rows: Row[] = [{ id: "1", name: "Jane" }];
    render(
      <Table
        columns={columns}
        rows={rows}
        getRowKey={(row) => row.id}
        pagination={{ count: 30, page: 1, pageSize: 25, onPageChange }}
      />,
    );

    expect(screen.getByText(/Page 1 of 2/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Previous" })).toBeDisabled();

    await user.click(screen.getByRole("button", { name: "Next" }));
    expect(onPageChange).toHaveBeenCalledWith(2);
  });
});
