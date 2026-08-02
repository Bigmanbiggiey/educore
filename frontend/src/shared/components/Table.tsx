import type { ReactNode } from "react";

import { Button } from "@/shared/components/Button";
import { EmptyState } from "@/shared/components/EmptyState";
import { cn } from "@/shared/utils/cn";

interface Column<T> {
  key: string;
  header: string;
  render: (row: T) => ReactNode;
  className?: string;
}

interface TablePagination {
  /** Total row count across every page — DRF's `count` field. */
  count: number;
  page: number;
  pageSize: number;
  onPageChange: (page: number) => void;
}

interface TableProps<T> {
  columns: Column<T>[];
  rows: T[];
  getRowKey: (row: T) => string;
  emptyMessage?: string;
  /** Matches DRF `PageNumberPagination`'s shape (docs/api-design.md §3) —
   * omit for an already-fully-loaded, unpaginated list (e.g. a dashboard
   * facade's plain array). */
  pagination?: TablePagination;
}

/**
 * The shared list-view primitive — sticky header + optional DRF-shaped
 * pagination + a required empty state, per docs/ui-guidelines.md. Search/
 * filter/bulk-action UI are deliberately not part of this first version:
 * nothing consuming `Table` yet needs them (Stage 2's dashboards are
 * read-only, unfiltered lists) — they land on top of this same component
 * once a real CRUD screen (Stage 3) needs them, not speculatively.
 */
export function Table<T>({ columns, rows, getRowKey, emptyMessage, pagination }: TableProps<T>) {
  if (rows.length === 0) {
    return <EmptyState message={emptyMessage ?? "Nothing to show here yet."} />;
  }

  const totalPages = pagination ? Math.max(1, Math.ceil(pagination.count / pagination.pageSize)) : 1;

  return (
    <div className="flex flex-col gap-3">
      <div className="max-h-[28rem] overflow-auto rounded-card border border-border">
        <table className="w-full border-collapse text-left text-sm">
          <thead className="sticky top-0 bg-surface-muted">
            <tr>
              {columns.map((column) => (
                <th
                  key={column.key}
                  scope="col"
                  className={cn("px-4 py-2 font-medium text-text/70", column.className)}
                >
                  {column.header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={getRowKey(row)} className="border-t border-border">
                {columns.map((column) => (
                  <td key={column.key} className={cn("px-4 py-2 text-text", column.className)}>
                    {column.render(row)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {pagination && (
        <div className="flex items-center justify-between text-sm text-text/70">
          <span>
            Page {pagination.page} of {totalPages} — {pagination.count} total
          </span>
          <div className="flex gap-2">
            <Button
              variant="outline"
              disabled={pagination.page <= 1}
              onClick={() => pagination.onPageChange(pagination.page - 1)}
            >
              Previous
            </Button>
            <Button
              variant="outline"
              disabled={pagination.page >= totalPages}
              onClick={() => pagination.onPageChange(pagination.page + 1)}
            >
              Next
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
