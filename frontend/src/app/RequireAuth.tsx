import { Navigate, Outlet, useNavigate } from "react-router-dom";

import { ActingAsBanner } from "@/shared/components/ActingAsBanner";
import { AppHeader } from "@/shared/components/AppHeader";

import { useAuth } from "./providers/AuthProvider";

/**
 * Client-side gate only, for UX (redirecting to /login) — never the
 * authorization boundary. The API enforces this regardless of what the
 * client renders (docs/frontend-architecture.md §1). Also supplies the
 * one shared header (with sign-out) every authenticated route gets, so
 * individual portal pages don't each reimplement it, plus the persistent
 * break-glass banner (docs/permissions.md §7) whenever a System Admin is
 * mid-act-as-session — rendered here so it's impossible to navigate
 * anywhere in the app without seeing it.
 */
export function RequireAuth() {
  const { status, user, logout, actingAsInstitution, endActAs } = useAuth();
  const navigate = useNavigate();

  if (status === "loading") {
    return (
      <div className="flex min-h-screen items-center justify-center text-text">Loading…</div>
    );
  }
  if (status === "unauthenticated") return <Navigate to="/login" replace />;

  async function handleExitActAs() {
    await endActAs();
    navigate("/system-admin");
  }

  return (
    <div className="flex min-h-screen flex-col">
      {actingAsInstitution && (
        <ActingAsBanner institutionName={actingAsInstitution.name} onExit={handleExitActAs} />
      )}
      <AppHeader userLabel={user?.email ?? user?.phone ?? undefined} onLogout={() => void logout()} />
      <Outlet />
    </div>
  );
}
