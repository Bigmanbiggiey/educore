import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";

import * as auth from "@/shared/lib/auth";
import type { MeResponse } from "@/shared/lib/auth";

type AuthStatus = "loading" | "authenticated" | "unauthenticated";

interface AuthContextValue {
  status: AuthStatus;
  user: MeResponse | null;
  /** Role names at the current request's institution — [] while loading
   * or unauthenticated, also [] if authenticated with no active
   * membership at this hostname (docs/permissions.md §6: a session can
   * outlive a mid-window-revoked membership). */
  roles: string[];
  login: (emailOrPhone: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

/**
 * On app boot, silently exchanges the httpOnly refresh cookie (if any) for
 * an access token before rendering any protected route, then loads the
 * current user — docs/frontend-architecture.md §2. Neither call happens
 * again on its own; `login`/`logout` below are the only other writers of
 * this state.
 */
export function AuthProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<AuthStatus>("loading");
  const [user, setUser] = useState<MeResponse | null>(null);

  const loadUser = useCallback(async () => {
    const me = await auth.fetchMe();
    setUser(me);
    setStatus("authenticated");
  }, []);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const refreshed = await auth.silentRefresh();
      if (cancelled) return;
      if (!refreshed) {
        setStatus("unauthenticated");
        return;
      }
      try {
        await loadUser();
      } catch {
        if (!cancelled) setStatus("unauthenticated");
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [loadUser]);

  const login = useCallback(
    async (emailOrPhone: string, password: string) => {
      await auth.login(emailOrPhone, password);
      await loadUser();
    },
    [loadUser],
  );

  const logout = useCallback(async () => {
    await auth.logout();
    setUser(null);
    setStatus("unauthenticated");
  }, []);

  const roles = user?.institution_membership?.roles ?? [];

  return (
    <AuthContext.Provider value={{ status, user, roles, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used within AuthProvider");
  return context;
}
