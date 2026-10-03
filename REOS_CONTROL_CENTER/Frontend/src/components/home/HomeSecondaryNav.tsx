import Link from "next/link";

const items = [
  ["PG", "/search?intent=pg"],
  ["Plot", "/search?intent=plot"],
  ["Localities", "/market"],
  ["Projects", "/project"],
  ["Home Loans", "#tools"],
  ["Interiors", "#services"],
  ["Tools", "#tools"],
  ["Advice", "#advice"],
  ["Help", "#help"],
] as const;

export function HomeSecondaryNav() {
  return (
    <nav
      className="home-secondary-nav"
      aria-label="HOMIO discovery navigation"
    >
      <div className="page-container home-secondary-nav__inner">
        <div className="home-secondary-nav__rail">
          {items.map(([label, href]) => (
            <Link key={label} href={href}>
              {label}
            </Link>
          ))}
        </div>
      </div>
    </nav>
  );
}
