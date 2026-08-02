import { forwardRef, type InputHTMLAttributes } from "react";

interface TextFieldProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  error?: string;
}

export const TextField = forwardRef<HTMLInputElement, TextFieldProps>(
  ({ label, error, id, name, ...props }, ref) => {
    const inputId = id ?? name;
    return (
      <div className="flex flex-col gap-1">
        <label htmlFor={inputId} className="text-sm font-medium text-text">
          {label}
        </label>
        <input
          id={inputId}
          name={name}
          ref={ref}
          aria-invalid={error ? true : undefined}
          aria-describedby={error ? `${inputId}-error` : undefined}
          className="rounded-input border border-border bg-surface px-3 py-2 text-text focus:outline-none focus:ring-2 focus:ring-primary"
          {...props}
        />
        {error && (
          <p id={`${inputId}-error`} role="alert" className="text-sm text-danger">
            {error}
          </p>
        )}
      </div>
    );
  },
);
TextField.displayName = "TextField";
