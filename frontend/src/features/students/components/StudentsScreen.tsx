import { useState } from "react";

import { Button } from "@/shared/components/Button";
import { ConfirmModal } from "@/shared/components/ConfirmModal";
import { Select } from "@/shared/components/Select";
import { TextField } from "@/shared/components/TextField";

import { useDeleteStudent } from "../api/useDeleteStudent";
import { DEFAULT_PAGE_SIZE, PAGE_SIZE_OPTIONS } from "../api/useStudents";
import type { Student } from "../types";
import { CreateStudentModal } from "./CreateStudentModal";
import { EditStudentModal } from "./EditStudentModal";
import { StudentsTable } from "./StudentsTable";

const SORT_OPTIONS = [
  { value: "", label: "Default order" },
  { value: "admission_number", label: "Admission number (A–Z)" },
  { value: "-admission_number", label: "Admission number (Z–A)" },
  { value: "last_name", label: "Last name (A–Z)" },
  { value: "-last_name", label: "Last name (Z–A)" },
  { value: "date_of_birth", label: "Date of birth (oldest first)" },
  { value: "-date_of_birth", label: "Date of birth (youngest first)" },
];

const PAGE_SIZE_SELECT_OPTIONS = PAGE_SIZE_OPTIONS.map((size) => ({
  value: String(size),
  label: `${size} per page`,
}));

export function StudentsScreen() {
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(DEFAULT_PAGE_SIZE);
  const [ordering, setOrdering] = useState("");
  const [search, setSearch] = useState("");
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [editingStudent, setEditingStudent] = useState<Student | null>(null);
  const [deletingStudent, setDeletingStudent] = useState<Student | null>(null);

  const { mutate: deleteStudent, isPending: isDeleting } = useDeleteStudent();

  function handleConfirmDelete() {
    if (!deletingStudent) return;
    deleteStudent(deletingStudent.id, { onSuccess: () => setDeletingStudent(null) });
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-text">Students</h2>
        <Button onClick={() => setCreateModalOpen(true)}>Add student</Button>
      </div>
      <div className="flex flex-wrap gap-4">
        <TextField
          label="Search"
          name="search"
          placeholder="Name or admission number"
          value={search}
          onChange={(event) => {
            setSearch(event.target.value);
            setPage(1);
          }}
        />
        <Select
          label="Sort by"
          name="sort-by"
          options={SORT_OPTIONS}
          value={ordering}
          onChange={(event) => {
            setOrdering(event.target.value);
            setPage(1);
          }}
        />
        <Select
          label="Page size"
          name="page-size"
          options={PAGE_SIZE_SELECT_OPTIONS}
          value={String(pageSize)}
          onChange={(event) => {
            setPageSize(Number(event.target.value));
            setPage(1);
          }}
        />
      </div>
      <StudentsTable
        page={page}
        pageSize={pageSize}
        ordering={ordering || undefined}
        search={search || undefined}
        onPageChange={setPage}
        onEdit={setEditingStudent}
        onDelete={setDeletingStudent}
      />
      <CreateStudentModal open={createModalOpen} onClose={() => setCreateModalOpen(false)} />
      <EditStudentModal student={editingStudent} onClose={() => setEditingStudent(null)} />
      <ConfirmModal
        open={deletingStudent !== null}
        title="Delete student"
        message={
          deletingStudent
            ? `Delete ${deletingStudent.first_name} ${deletingStudent.last_name}? This cannot be undone.`
            : ""
        }
        onConfirm={handleConfirmDelete}
        onCancel={() => setDeletingStudent(null)}
        isConfirming={isDeleting}
      />
    </div>
  );
}
