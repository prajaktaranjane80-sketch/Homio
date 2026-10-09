import Link from "next/link";

export function GlobalActionLayer() {
  return (
    <aside className="global-actions" aria-label="Global quick actions">
      <div className="global-actions__panel">
        <Link className="global-actions__link" href="/">
          Home
        </Link>

        <Link className="global-actions__link" href="/search">
          Search
        </Link>

        <Link
          className="global-actions__link"
          href="/project/homio-kalyani-residences-001"
        >
          Projects
        </Link>
      </div>
    </aside>
  );
}
