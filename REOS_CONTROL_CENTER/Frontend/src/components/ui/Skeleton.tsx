export function Skeleton({
  width,
  height = "16px",
  className = "",
}: Readonly<{
  width?: string;
  height?: string;
  className?: string;
}>) {
  return (
    <span
      className={`skeleton ${className}`.trim()}
      aria-hidden="true"
      style={{
        width: width ?? "100%",
        height,
      }}
    />
  );
}
