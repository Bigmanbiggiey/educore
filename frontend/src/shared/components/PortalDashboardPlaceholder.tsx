interface PortalDashboardPlaceholderProps {
  portalName: string;
}

/**
 * Every portal's `DashboardPage.tsx` renders this until that portal has
 * real widgets — an empty portal shell per docs/roadmap.md Phase 1's
 * "dashboard shell... no data yet" milestone. One shared placeholder
 * rather than 12 near-identical hand-rolled pages, per
 * docs/frontend-architecture.md §5: primitive UI belongs in
 * `shared/components`, not forked per portal.
 */
export function PortalDashboardPlaceholder({ portalName }: PortalDashboardPlaceholderProps) {
  return (
    <div className="flex flex-1 flex-col items-center justify-center gap-2 p-8 text-center">
      <h2 className="text-xl font-semibold text-text">{portalName} Dashboard</h2>
      <p className="text-text/70">Nothing to show here yet.</p>
    </div>
  );
}
