type NavigationItem = {
  label: string;
  href: string;
};

const foundationItems: NavigationItem[] = [
  {
    label: "Discover",
    href: "/",
  },
];

export function ResponsiveNavigation({
  items = foundationItems,
}: {
  items?: NavigationItem[];
}) {
  return (
    <div>
      <nav
        className="responsive-nav__desktop"
        aria-label="Primary navigation"
      >
        {items.map((item) => (
          <a className="responsive-nav__link" href={item.href} key={item.href}>
            {item.label}
          </a>
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
              <a href={item.href} key={item.href}>
                {item.label}
              </a>
            ))}
          </nav>
        </details>
      </div>
    </div>
  );
}
