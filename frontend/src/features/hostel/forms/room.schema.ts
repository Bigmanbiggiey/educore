import { z } from "zod";

export const roomSchema = z.object({
  room_number: z.string().min(1, "Enter a room number"),
  capacity: z
    .string()
    .min(1, "Enter a capacity")
    .refine((value) => Number.isInteger(Number(value)) && Number(value) > 0, "Capacity must be a positive whole number"),
});

export type RoomFormValues = z.infer<typeof roomSchema>;
