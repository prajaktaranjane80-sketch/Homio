export function GlobalActionLayer() {
  return (
    <aside className="global-actions" aria-label="Global quick actions">
      <div className="global-actions__panel">
        <a className="global-actions__link" href="#main-content">
          Home
        </a>

        <a className="global-actions__link" href="#experience">
          Experience
        </a>

        <a className="global-actions__link" href="#boundary">
          Boundary
        </a>
      </div>
    </aside>
  );
}