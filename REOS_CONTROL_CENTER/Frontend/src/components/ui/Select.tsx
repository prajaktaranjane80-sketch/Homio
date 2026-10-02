import type { ReactNode, SelectHTMLAttributes } from "react";

export function Select({
  label,
  hint,
  error,
  id,
  children,
  className = "",
  ...props
}: Readonly<
  SelectHTMLAttributes<HTMLSelectElement> & {
    label?: string;
    hint?: string;
    error?: string;
    children: ReactNode;
  }
>) {
  const selectId =
    id ?? `select-${label?.toLowerCase().replace(/\s+/g, "-") ?? "field"}`;

  return (
    <div className="field-group">
      {label ? (
        <label className="field-label" htmlFor={selectId}>
          {label}
        </label>
      ) : null}

      <select
        id={selectId}
        className={`select-field ${className}`.trim()}
        aria-invalid={error ? true : undefined}
        {...props}
      >
        {children}
      </select>

      {hint ? <span className="field-hint">{hint}</span> : null}

      {error ? (
        <span className="field-error" role="alert">
          {error}
        </span>
      ) : null}
    </div>
  );
}
