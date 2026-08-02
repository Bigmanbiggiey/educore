import { forwardRef, type SelectHTMLAttributes } from "react";

interface SelectOption {
  value: string;
  label: string;
}

interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label: string;
  error?: string;
  options: SelectOption[];
}

/** Mirrors `TextField`'s exact shape — same labeled/error/aria pattern,
 * for the handful of fixed-choice fields (payment method, borrower type,
 * loan return condition) forms need. */
export const Select = forwardRef<HTMLSelectElement, SelectProps>(
  ({ label, error, id, name, options, ...props }, ref) => {
    const selectId = id ?? name;
    return (
      <div className="flex flex-col gap-1">
        <label htmlFor={selectId} className="text-sm font-medium text-text">
          {label}
        </label>
        <select
          id={selectId}
          name={name}
          ref={ref}
          aria-invalid={error ? true : undefined}
          aria-describedby={error ? `${selectId}-error` : undefined}
          className="rounded-input border border-border bg-surface px-3 py-2 text-text focus:outline-none focus:ring-2 focus:ring-primary"
          {...props}
        >
          {options.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
        {error && (
          <p id={`${selectId}-error`} role="alert" className="text-sm text-danger">
            {error}
          </p>
        )}
      </div>
    );
  },
);
Select.displayName = "Select";
