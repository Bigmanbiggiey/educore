import { Button } from "@/shared/components/Button";
import { QueryBoundary } from "@/shared/components/QueryBoundary";
import { Table } from "@/shared/components/Table";

import { useRooms } from "../api/useRooms";
import type { Room } from "../types";

interface RoomsTableProps {
  page: number;
  pageSize: number;
  ordering?: string;
  onPageChange: (page: number) => void;
  onViewOccupancy: (roomId: string) => void;
  onAllocateBed: (roomId: string) => void;
  onEdit: (room: Room) => void;
  onDelete: (room: Room) => void;
}

export function RoomsTable({
  page,
  pageSize,
  ordering,
  onPageChange,
  onViewOccupancy,
  onAllocateBed,
  onEdit,
  onDelete,
}: RoomsTableProps) {
  const query = useRooms({ page, pageSize, ordering });

  const columns = [
    { key: "hostel", header: "Hostel", render: (row: Room) => row.hostel },
    { key: "room_number", header: "Room", render: (row: Room) => row.room_number },
    { key: "capacity", header: "Capacity", render: (row: Room) => row.capacity },
    {
      key: "actions",
      header: "",
      render: (row: Room) => (
        <div className="flex flex-wrap gap-2">
          <Button variant="outline" onClick={() => onViewOccupancy(row.id)}>
            View occupancy
          </Button>
          <Button variant="outline" onClick={() => onAllocateBed(row.id)}>
            Allocate bed
          </Button>
          <Button variant="secondary" onClick={() => onEdit(row)}>
            Edit
          </Button>
          <Button variant="danger" onClick={() => onDelete(row)}>
            Delete
          </Button>
        </div>
      ),
    },
  ];

  return (
    <QueryBoundary query={query}>
      {(data) => (
        <Table
          columns={columns}
          rows={data.results}
          getRowKey={(row) => row.id}
          emptyMessage="No hostel rooms set up yet."
          pagination={{ count: data.count, page, pageSize, onPageChange }}
        />
      )}
    </QueryBoundary>
  );
}
