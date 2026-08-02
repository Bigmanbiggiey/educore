import { useCurrentTerm } from "@/features/academic-terms";
import { Modal } from "@/shared/components/Modal";
import { QueryBoundary } from "@/shared/components/QueryBoundary";
import { StatTile } from "@/shared/components/StatTile";

import { useRoomOccupancy } from "../api/useRoomOccupancy";

interface OccupancyModalProps {
  roomId: string | null;
  onClose: () => void;
}

export function OccupancyModal({ roomId, onClose }: OccupancyModalProps) {
  const { data: currentTerm } = useCurrentTerm();
  const query = useRoomOccupancy(roomId, currentTerm?.id);

  return (
    <Modal open={roomId !== null} onClose={onClose} title="Room occupancy">
      {currentTerm ? (
        <QueryBoundary query={query}>
          {(data) => (
            <div className="grid grid-cols-3 gap-3">
              <StatTile label="Capacity" value={String(data.capacity)} />
              <StatTile label="Occupied" value={String(data.occupied)} />
              <StatTile label="Available" value={String(data.available)} />
            </div>
          )}
        </QueryBoundary>
      ) : (
        <p className="text-sm text-text/70">No current term is set up.</p>
      )}
    </Modal>
  );
}
