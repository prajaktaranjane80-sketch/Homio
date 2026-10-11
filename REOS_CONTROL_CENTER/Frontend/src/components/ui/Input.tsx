import { useId, type InputHTMLAttributes } from "react";

export function Input({
  label,
  hint,
  error,
  id,
  className = "",
  "aria-describedby": ariaDescribedBy,
  "aria-invalid": ariaInvalid,
  ...props
}: Readonly<
  InputHTMLAttributes<HTMLInputElement> & {
    label?: string;
    hint?: string;
    error?: string;
  }
>) {
  const generatedId = useId();
  const inputId = id ?? generatedId;

  const describedBy =
    [
      ariaDescribedBy,
      hint ? `${inputId}-hint` : "",
      error ? `${inputId}-error` : "",
    ]
      .filter(Boolean)
      .join(" ") || undefined;

  return (
    <div className="field-group">
      {label ? (
        <label className="field-label" htmlFor={inputId}>
          {label}
        </label>
      ) : null}

      <input
        id={inputId}
        className={`input-field ${className}`.trim()}
        aria-invalid={error ? true : ariaInvalid}
        aria-describedby={describedBy}
        {...props}
      />

      {hint ? (
        <span className="field-hint" id={`${inputId}-hint`}>
          {hint}
        </span>
      ) : null}

      {error ? (
        <span className="field-error" id={`${inputId}-error`} role="alert">
          {error}
        </span>
      ) : null}
    </div>
  );
}
