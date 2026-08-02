import type { components } from "@/shared/lib/api-types";

export type Room = components["schemas"]["Room"];
export type PaginatedRooms = components["schemas"]["PaginatedRoomList"];
export type BedAllocation = components["schemas"]["BedAllocation"];

// `RoomViewSet.occupancy` (backend/apps/hostel/views.py) returns
// `RoomOccupancySerializer(...).data`, not a `Room` — same generated-schema
// mismatch as `transport`'s manifest action (no `@extend_schema` override on
// the action, so drf-spectacular fell back to the viewset's `Room`
// serializer). Typed by hand against the real serializer
// (backend/apps/hostel/serializers.py).
export interface RoomOccupancy {
  capacity: number;
  occupied: number;
  available: number;
}

export interface AllocateBedInput {
  room: string;
  student_id: string;
  term_id: string;
}
