"use client";

import Link from "next/link";
import type { KeyboardEvent, MouseEvent } from "react";

type NavigationItem = {
  label: string;
  href: string;
};

const primaryItems: NavigationItem[] = [
  { label: "Buy", href: "/search?intent=buy" },
  { label: "Rent", href: "/search?intent=rent" },
  { label: "Commercial", href: "/search?intent=commercial" },
  { label: "Projects", href: "/search?intent=projects" },
  { label: "HOMIO AI", href: "/ai" },
];

function closeMobileMenu(event: MouseEvent<HTMLAnchorElement>): void {
  const disclosure = event.currentTarget
    .closest(".responsive-nav__mobile")
    ?.querySelector("details");

  if (disclosure) {
    disclosure.open = false;
  }
}

function closeMobileMenuOnEscape(
  event: KeyboardEvent<HTMLDetailsElement>,
): void {
  if (event.key !== "Escape" || !event.currentTarget.open) {
    return;
  }

  event.preventDefault();

  event.currentTarget.open = false;
  event.currentTarget.querySelector("summary")?.focus();
}

export function ResponsiveNavigation({
  items = primaryItems,
}: Readonly<{
  items?: NavigationItem[];
}>) {
  return (
    <div className="responsive-nav">
      <nav
        className="responsive-nav__desktop"
        aria-label="Primary navigation"
      >
        {items.map((item) => (
          <Link
            className="responsive-nav__link"
            href={item.href}
            key={item.href}
          >
            {item.label}
          </Link>
        ))}
      </nav>

      <div className="responsive-nav__mobile">
        <details onKeyDown={closeMobileMenuOnEscape}>
          <summary>Menu</summary>

          <nav
            className="responsive-nav__mobile-menu"
            aria-label="Mobile primary navigation"
          >
            {items.map((item) => (
              <Link
                href={item.href}
                key={item.href}
                onClick={closeMobileMenu}
              >
                {item.label}
              </Link>
            ))}
          </nav>
        </details>
      </div>
    </div>
  );
}
