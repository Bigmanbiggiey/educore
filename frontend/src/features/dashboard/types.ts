import type { components } from "@/shared/lib/api-types";

// Re-exported under feature-friendly names — the generated names are
// exact but verbose to reach for from every hook/component in this
// feature. Response shapes are generated (api-types.ts), never
// hand-written, per docs/api-design.md §9.
export type PrincipalDashboard = components["schemas"]["PrincipalDashboard"];
export type TeacherDashboard = components["schemas"]["TeacherDashboard"];
export type ParentDashboard = components["schemas"]["ParentDashboard"];
export type StudentDashboard = components["schemas"]["StudentDashboard"];
