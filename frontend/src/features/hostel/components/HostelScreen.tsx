import { useState } from "react";

import { AllocateBedModal } from "./AllocateBedModal";
import { OccupancyModal } from "./OccupancyModal";
import { RoomsTable } from "./RoomsTable";

export function HostelScreen() {
  const [page, setPage] = useState(1);
  const [occupancyRoomId, setOccupancyRoomId] = useState<string | null>(null);
  const [allocateRoomId, setAllocateRoomId] = useState<string | null>(null);

  return (
    <div className="flex flex-col gap-4">
      <h2 className="text-lg font-semibold text-text">Rooms</h2>
      <RoomsTable
        page={page}
        onPageChange={setPage}
        onViewOccupancy={setOccupancyRoomId}
        onAllocateBed={setAllocateRoomId}
      />
      <OccupancyModal roomId={occupancyRoomId} onClose={() => setOccupancyRoomId(null)} />
      <AllocateBedModal roomId={allocateRoomId} onClose={() => setAllocateRoomId(null)} />
    </div>
  );
}
