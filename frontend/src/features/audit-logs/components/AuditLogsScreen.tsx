import { useState } from "react";

import { Select } from "@/shared/components/Select";
import { TextField } from "@/shared/components/TextField";

import { DEFAULT_PAGE_SIZE, PAGE_SIZE_OPTIONS } from "../api/useAuditLogs";
import { AuditLogsTable } from "./AuditLogsTable";

const PAGE_SIZE_SELECT_OPTIONS = PAGE_SIZE_OPTIONS.map((size) => ({
  value: String(size),
  label: `${size} per page`,
}));

export function AuditLogsScreen() {
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(DEFAULT_PAGE_SIZE);
  const [institution, setInstitution] = useState("");
  const [actor, setActor] = useState("");
  const [action, setAction] = useState("");

  function resetToFirstPage() {
    setPage(1);
  }

  return (
    <div className="flex flex-col gap-4">
      <h2 className="text-lg font-semibold text-text">Audit log</h2>
      <div className="flex flex-wrap gap-4">
        <TextField
          label="Institution ID"
          name="institution-filter"
          value={institution}
          onChange={(event) => {
            setInstitution(event.target.value);
            resetToFirstPage();
          }}
        />
        <TextField
          label="Actor ID"
          name="actor-filter"
          value={actor}
          onChange={(event) => {
            setActor(event.target.value);
            resetToFirstPage();
          }}
        />
        <TextField
          label="Action contains"
          name="action-filter"
          value={action}
          onChange={(event) => {
            setAction(event.target.value);
            resetToFirstPage();
          }}
        />
        <Select
          label="Page size"
          name="page-size"
          options={PAGE_SIZE_SELECT_OPTIONS}
          value={String(pageSize)}
          onChange={(event) => {
            setPageSize(Number(event.target.value));
            resetToFirstPage();
          }}
        />
      </div>
      <AuditLogsTable
        page={page}
        pageSize={pageSize}
        institution={institution || undefined}
        actor={actor || undefined}
        action={action || undefined}
        onPageChange={setPage}
      />
    </div>
  );
}
