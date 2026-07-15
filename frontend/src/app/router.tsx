import { createBrowserRouter } from "react-router-dom";

/**
 * Portal subtrees are registered here as lazy-loaded routes starting
 * Phase 1 (docs/frontend-architecture.md §1):
 *   { path: "/:portalSlug/*", lazy: () => import("@/portals/<slug>/routes") }
 */
export const router = createBrowserRouter([
  {
    path: "/",
    element: (
      <div className="flex min-h-screen items-center justify-center">
        <h1 className="text-2xl font-semibold">EduCore</h1>
      </div>
    ),
  },
]);
