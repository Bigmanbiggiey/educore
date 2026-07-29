interface AppHeaderProps {
  userLabel?: string;
  onLogout: () => void;
}

/** Chrome wrapped around every authenticated route by `app/RequireAuth.tsx`
 * — lives here (not in `app/`) so it stays presentational and reusable,
 * with auth state passed in as props rather than read from context
 * (`shared` may not import from `app`, docs/frontend-architecture.md §5). */
export function AppHeader({ userLabel, onLogout }: AppHeaderProps) {
  return (
    <header className="flex items-center justify-between border-b border-border bg-surface px-6 py-4">
      <span className="font-semibold text-text">EduCore</span>
      <div className="flex items-center gap-4">
        {userLabel && <span className="text-sm text-text/70">{userLabel}</span>}
        <button
          type="button"
          onClick={onLogout}
          className="text-sm text-primary hover:underline"
        >
          Sign out
        </button>
      </div>
    </header>
  );
}
