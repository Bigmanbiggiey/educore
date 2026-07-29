import { Navigate, Outlet } from "react-router-dom";

import { AppHeader } from "@/shared/components/AppHeader";

import { useAuth } from "./providers/AuthProvider";

/**
 * Client-side gate only, for UX (redirecting to /login) — never the
 * authorization boundary. The API enforces this regardless of what the
 * client renders (docs/frontend-architecture.md §1). Also supplies the
 * one shared header (with sign-out) every authenticated route gets, so
 * individual portal pages don't each reimplement it.
 */
export function RequireAuth() {
  const { status, user, logout } = useAuth();

  if (status === "loading") {
    return (
      <div className="flex min-h-screen items-center justify-center text-text">Loading…</div>
    );
  }
  if (status === "unauthenticated") return <Navigate to="/login" replace />;

  return (
    <div className="flex min-h-screen flex-col">
      <AppHeader userLabel={user?.email ?? user?.phone ?? undefined} onLogout={() => void logout()} />
      <Outlet />
    </div>
  );
}
