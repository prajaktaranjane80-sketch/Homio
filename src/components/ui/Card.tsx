import type { HTMLAttributes, ReactNode } from "react";

export function Card({
  children,
  className = "",
  ...props
}: Readonly<HTMLAttributes<HTMLElement> & { children: ReactNode }>) {
  return (
    <article className={`card ${className}`.trim()} {...props}>
      {children}
    </article>
  );
}
