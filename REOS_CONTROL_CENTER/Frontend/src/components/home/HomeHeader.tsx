import Link from "next/link";

const primaryLinks = [
  ["Buy", "/search?intent=buy"],
  ["Rent", "/search?intent=rent"],
  ["New Projects", "/search?intent=new-projects"],
  ["Commercial", "/search?intent=commercial"],
  ["Saved", "/saved"],
  ["My HOMIO", "/my"],
] as const;

export function HomeHeader() {
  return (
    <header className="home-header">
      <div className="home-header__inner">
        <Link className="home-brand" href="/" aria-label="HOMIO home">
          <span className="home-brand__name">HOMIO</span>
          <span className="home-brand__descriptor">
            REAL ESTATE, SIMPLIFIED
          </span>
        </Link>

        <nav
          className="home-header__desktop"
          aria-label="HOMIO primary navigation"
        >
          {primaryLinks.map(([label, href]) => (
            <Link key={href} href={href} className="home-header__link">
              {label}
            </Link>
          ))}

          <Link href="#post-property" className="home-header__post">
            Post Property
          </Link>
        </nav>

        <div className="home-header__mobile">
          <details>
            <summary>Menu</summary>

            <nav aria-label="HOMIO mobile navigation">
              {primaryLinks.map(([label, href]) => (
                <Link key={href} href={href}>
                  {label}
                </Link>
              ))}

              <Link href="#post-property">Post Property</Link>
            </nav>
          </details>
        </div>
      </div>
    </header>
  );
}
