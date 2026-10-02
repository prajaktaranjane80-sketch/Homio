import type { InputHTMLAttributes } from "react";

export function SearchField({
  className = "",
  ...props
}: Readonly<InputHTMLAttributes<HTMLInputElement>>) {
  return (
    <input
      type="search"
      className={`search-field ${className}`.trim()}
      autoComplete="off"
      {...props}
    />
  );
}
