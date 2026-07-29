import { createBrowserRouter } from "react-router-dom";

import { ForgotPasswordPage } from "./pages/ForgotPasswordPage";
import { LoginPage } from "./pages/LoginPage";
import { PostLoginRedirect } from "./pages/PostLoginRedirect";
import { ResetPasswordPage } from "./pages/ResetPasswordPage";
import { RequireAuth } from "./RequireAuth";
import { RequireRole } from "./RequireRole";

// One entry per portal, each with a statically-written `import()` so Vite
// code-splits per portal (docs/frontend-architecture.md §1: "a Librarian's
// session never downloads Payroll or Hostel bundles") — a single
// `/:portalSlug/*` route with a runtime-computed import path can't be
// statically analyzed for chunking, so this is 12 explicit entries rather
// than a loop building the import call itself.
//
// "system-admin" has no entry here: that access model is
// `is_platform_staff`, not an `InstitutionMembership`/role
// (docs/permissions.md §7's "break glass" flow), so there's no role to
// guard it with yet — the portal folder exists for structural
// completeness only until that backend flow is built.
const PORTAL_ROUTES = [
  {
    path: "/institution-admin",
    roles: ["Institution Administrator"],
    lazy: () => import("@/portals/institution-admin/routes"),
  },
  {
    path: "/principal",
    roles: ["Principal", "Deputy Principal"],
    lazy: () => import("@/portals/principal/routes"),
  },
  {
    path: "/finance-officer",
    roles: ["Finance Officer"],
    lazy: () => import("@/portals/finance-officer/routes"),
  },
  { path: "/teacher", roles: ["Teacher"], lazy: () => import("@/portals/teacher/routes") },
  { path: "/parent", roles: ["Parent"], lazy: () => import("@/portals/parent/routes") },
  { path: "/student", roles: ["Student"], lazy: () => import("@/portals/student/routes") },
  {
    path: "/librarian",
    roles: ["Librarian"],
    lazy: () => import("@/portals/librarian/routes"),
  },
  { path: "/nurse", roles: ["Nurse"], lazy: () => import("@/portals/nurse/routes") },
  {
    path: "/receptionist",
    roles: ["Receptionist"],
    lazy: () => import("@/portals/receptionist/routes"),
  },
  {
    path: "/transport-manager",
    roles: ["Transport Manager"],
    lazy: () => import("@/portals/transport-manager/routes"),
  },
  {
    path: "/hostel-warden",
    roles: ["Hostel Warden"],
    lazy: () => import("@/portals/hostel-warden/routes"),
  },
];

export const router = createBrowserRouter([
  { path: "/login", element: <LoginPage /> },
  { path: "/forgot-password", element: <ForgotPasswordPage /> },
  { path: "/reset-password", element: <ResetPasswordPage /> },
  {
    element: <RequireAuth />,
    children: [
      { path: "/", element: <PostLoginRedirect /> },
      ...PORTAL_ROUTES.map(({ path, roles, lazy }) => ({
        path,
        element: <RequireRole roles={roles} />,
        children: [{ index: true, lazy }],
      })),
    ],
  },
]);
