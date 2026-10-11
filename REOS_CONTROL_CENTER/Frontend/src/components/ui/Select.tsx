import {
  useId,
  type ReactNode,
  type SelectHTMLAttributes,
} from "react";

export function Select({
  label,
  hint,
  error,
  id,
  children,
  className = "",
  "aria-describedby": ariaDescribedBy,
  "aria-invalid": ariaInvalid,
  ...props
}: Readonly<
  SelectHTMLAttributes<HTMLSelectElement> & {
    label?: string;
    hint?: string;
    error?: string;
    children: ReactNode;
  }
>) {
  const generatedId = useId();
  const selectId = id ?? generatedId;
  const hintId = `${selectId}-hint`;
  const errorId = `${selectId}-error`;

  const describedBy =
    [
      ariaDescribedBy,
      hint ? hintId : "",
      error ? errorId : "",
    ]
      .filter(Boolean)
      .join(" ") || undefined;

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
        aria-invalid={error ? true : ariaInvalid}
        aria-describedby={describedBy}
        {...props}
      >
        {children}
      </select>

      {hint ? (
        <span className="field-hint" id={hintId}>
          {hint}
        </span>
      ) : null}

      {error ? (
        <span className="field-error" id={errorId} role="alert">
          {error}
        </span>
      ) : null}
    </div>
  );
}
