import { useState } from "react";

import { ConfirmModal } from "@/shared/components/ConfirmModal";
import { Select } from "@/shared/components/Select";

import { DEFAULT_PAGE_SIZE, PAGE_SIZE_OPTIONS } from "../api/useRooms";
import { useDeleteRoom } from "../api/useDeleteRoom";
import type { Room } from "../types";
import { AllocateBedModal } from "./AllocateBedModal";
import { EditRoomModal } from "./EditRoomModal";
import { OccupancyModal } from "./OccupancyModal";
import { RoomsTable } from "./RoomsTable";

const SORT_OPTIONS = [
  { value: "", label: "Default order" },
  { value: "room_number", label: "Room number (A–Z)" },
  { value: "-room_number", label: "Room number (Z–A)" },
];

const PAGE_SIZE_SELECT_OPTIONS = PAGE_SIZE_OPTIONS.map((size) => ({
  value: String(size),
  label: `${size} per page`,
}));

export function HostelScreen() {
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(DEFAULT_PAGE_SIZE);
  const [ordering, setOrdering] = useState("");
  const [occupancyRoomId, setOccupancyRoomId] = useState<string | null>(null);
  const [allocateRoomId, setAllocateRoomId] = useState<string | null>(null);
  const [editingRoom, setEditingRoom] = useState<Room | null>(null);
  const [deletingRoom, setDeletingRoom] = useState<Room | null>(null);

  const { mutate: deleteRoom, isPending: isDeleting } = useDeleteRoom();

  function handleConfirmDelete() {
    if (!deletingRoom) return;
    deleteRoom(deletingRoom.id, { onSuccess: () => setDeletingRoom(null) });
  }

  return (
    <div className="flex flex-col gap-4">
      <h2 className="text-lg font-semibold text-text">Rooms</h2>
      <div className="flex flex-wrap gap-4">
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
      <RoomsTable
        page={page}
        pageSize={pageSize}
        ordering={ordering || undefined}
        onPageChange={setPage}
        onViewOccupancy={setOccupancyRoomId}
        onAllocateBed={setAllocateRoomId}
        onEdit={setEditingRoom}
        onDelete={setDeletingRoom}
      />
      <OccupancyModal roomId={occupancyRoomId} onClose={() => setOccupancyRoomId(null)} />
      <AllocateBedModal roomId={allocateRoomId} onClose={() => setAllocateRoomId(null)} />
      <EditRoomModal room={editingRoom} onClose={() => setEditingRoom(null)} />
      <ConfirmModal
        open={deletingRoom !== null}
        title="Delete room"
        message={deletingRoom ? `Delete room "${deletingRoom.room_number}"? This cannot be undone.` : ""}
        onConfirm={handleConfirmDelete}
        onCancel={() => setDeletingRoom(null)}
        isConfirming={isDeleting}
      />
    </div>
  );
}
