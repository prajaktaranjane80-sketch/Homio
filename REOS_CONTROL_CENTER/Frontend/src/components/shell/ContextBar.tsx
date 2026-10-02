export function ContextBar({
  primary,
  secondary,
}: Readonly<{
  primary: string;
  secondary: string;
}>) {
  return (
    <div className="context-bar">
      <div className="context-bar__inner">
        <span className="context-bar__primary">{primary}</span>
        <span className="context-bar__secondary">{secondary}</span>
      </div>
    </div>
  );
}
