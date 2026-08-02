import { QueryBoundary } from "@/shared/components/QueryBoundary";
import { Table } from "@/shared/components/Table";

import { useTeacherDashboard } from "../api/useTeacherDashboard";
import { DAY_NAMES } from "../format";
import type { TeacherDashboard as TeacherDashboardData } from "../types";

type ScheduleEntry = TeacherDashboardData["schedule"][number];

const columns = [
  {
    key: "day",
    header: "Day",
    render: (row: ScheduleEntry) => DAY_NAMES[row.day_of_week] ?? row.day_of_week,
  },
  {
    key: "time",
    header: "Time",
    render: (row: ScheduleEntry) => `${row.start_time.slice(0, 5)}–${row.end_time.slice(0, 5)}`,
  },
  { key: "room", header: "Room", render: (row: ScheduleEntry) => row.room || "—" },
];

export function TeacherDashboard() {
  const query = useTeacherDashboard();

  return (
    <QueryBoundary query={query}>
      {(data) => (
        <div className="flex flex-col gap-4">
          <h2 className="text-lg font-semibold text-text">My schedule</h2>
          <Table
            columns={columns}
            rows={data.schedule}
            getRowKey={(row) => `${row.day_of_week}-${row.start_time}-${row.subject_id}`}
            emptyMessage="No periods assigned yet."
          />
        </div>
      )}
    </QueryBoundary>
  );
}
