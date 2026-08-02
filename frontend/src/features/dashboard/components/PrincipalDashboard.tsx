import { QueryBoundary } from "@/shared/components/QueryBoundary";
import { StatTile } from "@/shared/components/StatTile";

import { usePrincipalDashboard } from "../api/usePrincipalDashboard";
import { formatPercent } from "../format";

export function PrincipalDashboard() {
  const query = usePrincipalDashboard();

  return (
    <QueryBoundary query={query}>
      {(data) => (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <StatTile label="Classes this term" value={String(data.class_count)} />
          <StatTile
            label="Average attendance rate"
            value={formatPercent(data.average_attendance_rate)}
            tone={
              data.average_attendance_rate !== null && Number(data.average_attendance_rate) < 0.75
                ? "warning"
                : "success"
            }
          />
          <StatTile
            label="Average fee collection rate"
            value={formatPercent(data.average_collection_rate)}
            tone={
              data.average_collection_rate !== null && Number(data.average_collection_rate) < 0.75
                ? "warning"
                : "success"
            }
          />
        </div>
      )}
    </QueryBoundary>
  );
}
