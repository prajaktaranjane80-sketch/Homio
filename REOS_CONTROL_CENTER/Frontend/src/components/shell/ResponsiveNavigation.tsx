import Link from "next/link";

type NavigationItem = {
  label: string;
  href: string;
};

const foundationItems: NavigationItem[] = [
  {
    label: "Experience",
    href: "#experience",
  },
  {
    label: "Boundary",
    href: "#boundary",
  },
];

export function ResponsiveNavigation({
  items = foundationItems,
}: {
  items?: NavigationItem[];
}) {
  return (
    <div>
      <nav className="responsive-nav__desktop" aria-label="Primary navigation">
        {items.map((item) => (
          <Link className="responsive-nav__link" href={item.href} key={item.href}>
            {item.label}
          </Link>
        ))}
      </nav>

      <div className="responsive-nav__mobile">
        <details>
          <summary>Menu</summary>

          <nav
            className="responsive-nav__mobile-menu"
            aria-label="Mobile primary navigation"
          >
            {items.map((item) => (
              <Link href={item.href} key={item.href}>
                {item.label}
              </Link>
            ))}
          </nav>
        </details>
      </div>
    </div>
  );
}