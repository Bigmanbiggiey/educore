/**
 * Small formatting helpers local to this feature — not promoted to
 * `shared/utils` speculatively; they land there once a second feature
 * genuinely needs the same formatting (`shared/utils` is empty today for
 * exactly this reason).
 */

export function formatPercent(value: string | number | null): string {
  if (value === null) return "—";
  const rate = typeof value === "string" ? Number(value) : value;
  return `${Math.round(rate * 100)}%`;
}

export function formatCurrency(value: string): string {
  return new Intl.NumberFormat("en-KE", { style: "currency", currency: "KES" }).format(
    Number(value),
  );
}

export const DAY_NAMES = [
  "Monday",
  "Tuesday",
  "Wednesday",
  "Thursday",
  "Friday",
  "Saturday",
  "Sunday",
];
