import { Card } from "@/shared/components/Card";
import { cn } from "@/shared/utils/cn";

interface StatTileProps {
  label: string;
  /** Pre-formatted for display (e.g. "82%", "KES 12,400") — formatting
   * varies too much by resource (percentages, currency, counts) to bake a
   * single formatter into the shared component. */
  value: string;
  /** Rendered under the value in a muted tone — a period/scope hint
   * ("this term"), not necessarily a trend delta. */
  helpText?: string;
  tone?: "neutral" | "success" | "warning" | "danger";
}

const VALUE_TONES: Record<NonNullable<StatTileProps["tone"]>, string> = {
  neutral: "text-text",
  success: "text-success",
  warning: "text-warning",
  danger: "text-danger",
};

/** The "number in a box" dashboard primitive — every portal's summary
 * dashboard is built from a row of these plus a table or two. */
export function StatTile({ label, value, helpText, tone = "neutral" }: StatTileProps) {
  return (
    <Card className="flex flex-col gap-1">
      <span className="text-sm font-medium text-text/70">{label}</span>
      <span className={cn("text-2xl font-semibold", VALUE_TONES[tone])}>{value}</span>
      {helpText && <span className="text-xs text-text/50">{helpText}</span>}
    </Card>
  );
}
