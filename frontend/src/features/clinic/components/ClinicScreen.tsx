import { useState } from "react";

import { Button } from "@/shared/components/Button";
import { ConfirmModal } from "@/shared/components/ConfirmModal";
import { Select } from "@/shared/components/Select";
import { TextField } from "@/shared/components/TextField";

import { DEFAULT_PAGE_SIZE, PAGE_SIZE_OPTIONS } from "../api/useClinicVisits";
import { useDeleteClinicVisit } from "../api/useDeleteClinicVisit";
import type { ClinicVisit } from "../types";
import { EditVisitModal } from "./EditVisitModal";
import { RecordVisitModal } from "./RecordVisitModal";
import { VisitsTable } from "./VisitsTable";

const SORT_OPTIONS = [
  { value: "", label: "Default order" },
  { value: "visit_date", label: "Visit date (earliest first)" },
  { value: "-visit_date", label: "Visit date (latest first)" },
];

const PAGE_SIZE_SELECT_OPTIONS = PAGE_SIZE_OPTIONS.map((size) => ({
  value: String(size),
  label: `${size} per page`,
}));

export function ClinicScreen() {
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(DEFAULT_PAGE_SIZE);
  const [ordering, setOrdering] = useState("");
  const [studentId, setStudentId] = useState("");
  const [visitDate, setVisitDate] = useState("");
  const [search, setSearch] = useState("");
  const [modalOpen, setModalOpen] = useState(false);
  const [editingVisit, setEditingVisit] = useState<ClinicVisit | null>(null);
  const [deletingVisit, setDeletingVisit] = useState<ClinicVisit | null>(null);

  const { mutate: deleteVisit, isPending: isDeleting } = useDeleteClinicVisit();

  function resetToFirstPage() {
    setPage(1);
  }

  function handleConfirmDelete() {
    if (!deletingVisit) return;
    deleteVisit(deletingVisit.id, { onSuccess: () => setDeletingVisit(null) });
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-text">Clinic visits</h2>
        <Button onClick={() => setModalOpen(true)}>Record visit</Button>
      </div>
      <div className="flex flex-wrap gap-4">
        <TextField
          label="Search"
          name="search"
          placeholder="Notes"
          value={search}
          onChange={(event) => {
            setSearch(event.target.value);
            resetToFirstPage();
          }}
        />
        <TextField
          label="Student ID"
          name="student-id-filter"
          value={studentId}
          onChange={(event) => {
            setStudentId(event.target.value);
            resetToFirstPage();
          }}
        />
        <TextField
          label="Visit date"
          name="visit-date-filter"
          type="date"
          value={visitDate}
          onChange={(event) => {
            setVisitDate(event.target.value);
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
      <VisitsTable
        page={page}
        pageSize={pageSize}
        ordering={ordering || undefined}
        studentId={studentId || undefined}
        visitDate={visitDate || undefined}
        search={search || undefined}
        onPageChange={setPage}
        onEdit={setEditingVisit}
        onDelete={setDeletingVisit}
      />
      <RecordVisitModal open={modalOpen} onClose={() => setModalOpen(false)} />
      <EditVisitModal visit={editingVisit} onClose={() => setEditingVisit(null)} />
      <ConfirmModal
        open={deletingVisit !== null}
        title="Delete visit"
        message="Delete this clinic visit record? This cannot be undone."
        onConfirm={handleConfirmDelete}
        onCancel={() => setDeletingVisit(null)}
        isConfirming={isDeleting}
      />
    </div>
  );
}
