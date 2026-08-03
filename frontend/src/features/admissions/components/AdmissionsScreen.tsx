import { useState } from "react";

import { Select } from "@/shared/components/Select";

import { DEFAULT_PAGE_SIZE, PAGE_SIZE_OPTIONS } from "../api/useApplications";
import type { Application } from "../types";
import { ApplicationsTable } from "./ApplicationsTable";
import { ConvertToEnrollmentModal } from "./ConvertToEnrollmentModal";
import { EditApplicationModal } from "./EditApplicationModal";

const STAGE_OPTIONS = [
  { value: "", label: "All stages" },
  { value: "submitted", label: "Submitted" },
  { value: "under_review", label: "Under review" },
  { value: "offered", label: "Offered" },
  { value: "accepted", label: "Accepted" },
  { value: "enrolled", label: "Enrolled" },
  { value: "rejected", label: "Rejected" },
  { value: "withdrawn", label: "Withdrawn" },
];

const SORT_OPTIONS = [
  { value: "", label: "Default order" },
  { value: "created_at", label: "Oldest first" },
  { value: "-created_at", label: "Newest first" },
  { value: "stage", label: "Stage (A–Z)" },
  { value: "-stage", label: "Stage (Z–A)" },
];

const PAGE_SIZE_SELECT_OPTIONS = PAGE_SIZE_OPTIONS.map((size) => ({
  value: String(size),
  label: `${size} per page`,
}));

export function AdmissionsScreen() {
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(DEFAULT_PAGE_SIZE);
  const [ordering, setOrdering] = useState("");
  const [stage, setStage] = useState<Application["stage"] | "">("");
  const [convertingApplicationId, setConvertingApplicationId] = useState<string | null>(null);
  const [editingApplication, setEditingApplication] = useState<Application | null>(null);

  function resetToFirstPage() {
    setPage(1);
  }

  return (
    <div className="flex flex-col gap-4">
      <h2 className="text-lg font-semibold text-text">Applications</h2>
      <div className="flex flex-wrap gap-4">
        <Select
          label="Stage"
          name="stage-filter"
          options={STAGE_OPTIONS}
          value={stage}
          onChange={(event) => {
            setStage(event.target.value as Application["stage"] | "");
            resetToFirstPage();
          }}
        />
        <Select
          label="Sort by"
          name="sort-by"
          options={SORT_OPTIONS}
          value={ordering}
          onChange={(event) => {
            setOrdering(event.target.value);
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
      <ApplicationsTable
        page={page}
        pageSize={pageSize}
        ordering={ordering || undefined}
        stage={stage || undefined}
        onPageChange={setPage}
        onConvertToEnrollment={setConvertingApplicationId}
        onEdit={setEditingApplication}
      />
      <ConvertToEnrollmentModal
        applicationId={convertingApplicationId}
        onClose={() => setConvertingApplicationId(null)}
      />
      <EditApplicationModal application={editingApplication} onClose={() => setEditingApplication(null)} />
    </div>
  );
}
