import { useCurrentTerm } from "@/features/academic-terms";
import { Button } from "@/shared/components/Button";
import { Modal } from "@/shared/components/Modal";
import { QueryBoundary } from "@/shared/components/QueryBoundary";
import { StatTile } from "@/shared/components/StatTile";
import { Table } from "@/shared/components/Table";

import { useDeleteBedAllocation } from "../api/useDeleteBedAllocation";
import { useRoomAllocations, type BedAllocation } from "../api/useRoomAllocations";
import { useRoomOccupancy } from "../api/useRoomOccupancy";

interface OccupancyModalProps {
  roomId: string | null;
  onClose: () => void;
}

export function OccupancyModal({ roomId, onClose }: OccupancyModalProps) {
  const { data: currentTerm } = useCurrentTerm();
  const occupancyQuery = useRoomOccupancy(roomId, currentTerm?.id);
  const allocationsQuery = useRoomAllocations(roomId, currentTerm?.id);
  const { mutate: removeAllocation, isPending, variables: removingId } = useDeleteBedAllocation();

  const columns = [
    { key: "student", header: "Student", render: (row: BedAllocation) => row.student_id },
    {
      key: "actions",
      header: "",
      render: (row: BedAllocation) => (
        <Button
          variant="danger"
          disabled={isPending && removingId === row.id}
          onClick={() => removeAllocation(row.id)}
        >
          Remove
        </Button>
      ),
    },
  ];

  return (
    <Modal open={roomId !== null} onClose={onClose} title="Room occupancy">
      {currentTerm ? (
        <div className="flex flex-col gap-4">
          <QueryBoundary query={occupancyQuery}>
            {(data) => (
              <div className="grid grid-cols-3 gap-3">
                <StatTile label="Capacity" value={String(data.capacity)} />
                <StatTile label="Occupied" value={String(data.occupied)} />
                <StatTile label="Available" value={String(data.available)} />
              </div>
            )}
          </QueryBoundary>
          <QueryBoundary query={allocationsQuery}>
            {(data) => (
              <Table
                columns={columns}
                rows={data.results}
                getRowKey={(row) => row.id}
                emptyMessage="No students allocated to this room yet."
              />
            )}
          </QueryBoundary>
        </div>
      ) : (
        <p className="text-sm text-text/70">No current term is set up.</p>
      )}
    </Modal>
  );
}
