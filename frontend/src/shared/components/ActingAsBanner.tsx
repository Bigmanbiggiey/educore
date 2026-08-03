interface ActingAsBannerProps {
  institutionName: string;
  onExit: () => void;
}

/**
 * The "impossible-to-miss" banner docs/permissions.md §7 requires for the
 * entire duration of a break-glass act-as session — rendered inside
 * `RequireAuth` whenever `actingAsInstitution` is set, never optional or
 * dismissible short of actually ending the session.
 */
export function ActingAsBanner({ institutionName, onExit }: ActingAsBannerProps) {
  return (
    <div className="flex items-center justify-between gap-4 bg-danger px-4 py-2 text-sm text-white">
      <span className="font-medium">
        Viewing as System Admin inside {institutionName}
      </span>
      <button
        type="button"
        onClick={onExit}
        className="rounded-button border border-white/50 px-3 py-1 hover:bg-white/10"
      >
        Exit
      </button>
    </div>
  );
}
