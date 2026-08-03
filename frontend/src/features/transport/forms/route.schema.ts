import { z } from "zod";

export const routeSchema = z.object({
  name: z.string().min(1, "Enter a route name"),
  vehicle: z.string().uuid("Enter a valid vehicle ID"),
});

export type RouteFormValues = z.infer<typeof routeSchema>;
