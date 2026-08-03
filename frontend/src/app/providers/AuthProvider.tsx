import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";

import * as auth from "@/shared/lib/auth";
import type { MeResponse } from "@/shared/lib/auth";

type AuthStatus = "loading" | "authenticated" | "unauthenticated";

interface ActingAsInstitution {
  id: string;
  name: string;
}

interface AuthContextValue {
  status: AuthStatus;
  user: MeResponse | null;
  /** Role names at the current request's institution — [] while loading
   * or unauthenticated, also [] if authenticated with no active
   * membership at this hostname (docs/permissions.md §6: a session can
   * outlive a mid-window-revoked membership). */
  roles: string[];
  /** docs/permissions.md §7 — granted via `is_platform_staff`, never a
   * role, so it's tracked separately from `roles` above. */
  isPlatformStaff: boolean;
  /** Set for the duration of a break-glass act-as session
   * (docs/permissions.md §7) — non-null means every request is currently
   * running with elevated, time-boxed access to this one institution. */
  actingAsInstitution: ActingAsInstitution | null;
  login: (emailOrPhone: string, password: string) => Promise<void>;
  platformLogin: (emailOrPhone: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  actAs: (institutionId: string, institutionName: string) => Promise<void>;
  endActAs: () => Promise<void>;
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
  const [actingAsInstitution, setActingAsInstitution] = useState<ActingAsInstitution | null>(
    null,
  );
  // Not state — restoring it never needs to trigger a re-render, and it
  // should never itself be treated as something the UI reads.
  const stashedToken = useRef<string | null>(null);

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

  const platformLogin = useCallback(
    async (emailOrPhone: string, password: string) => {
      await auth.platformLogin(emailOrPhone, password);
      await loadUser();
    },
    [loadUser],
  );

  const logout = useCallback(async () => {
    await auth.logout();
    setUser(null);
    setActingAsInstitution(null);
    setStatus("unauthenticated");
  }, []);

  const actAs = useCallback(async (institutionId: string, institutionName: string) => {
    stashedToken.current = auth.getAccessToken();
    const elevatedToken = await auth.actAs(institutionId);
    auth.setAccessToken(elevatedToken);
    setActingAsInstitution({ id: institutionId, name: institutionName });
  }, []);

  const endActAs = useCallback(async () => {
    try {
      await auth.endActAs();
    } finally {
      auth.setAccessToken(stashedToken.current);
      stashedToken.current = null;
      setActingAsInstitution(null);
    }
  }, []);

  const roles = user?.institution_membership?.roles ?? [];
  const isPlatformStaff = user?.is_platform_staff ?? false;

  return (
    <AuthContext.Provider
      value={{
        status,
        user,
        roles,
        isPlatformStaff,
        actingAsInstitution,
        login,
        platformLogin,
        logout,
        actAs,
        endActAs,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used within AuthProvider");
  return context;
}
