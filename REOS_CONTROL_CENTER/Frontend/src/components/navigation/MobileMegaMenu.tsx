"use client";

import Link from "next/link";
import { useId, useState } from "react";

import styles from "./GlobalMenus.module.css";

const groups = [
  {
    title: "Explore",
    href: "/search",
    description: "Homes, commercial properties and projects",
  },
  {
    title: "Markets",
    href: "/search?city=Pune",
    description: "Market context and configured locations",
  },
  {
    title: "Intelligence",
    href: "/ai",
    description: "Property insights and HOMIO AI",
  },
  {
    title: "Services",
    href: "/enquiry",
    description: "Enquiries and available service pathways",
  },
  {
    title: "My HOMIO",
    href: "/my",
    description: "Your account and saved discovery",
  },
  {
    title: "Professional",
    href: "/pro",
    description: "Protected professional workspace preview",
  },
] as const;

export default function MobileMegaMenu() {
  const [open, setOpen] = useState(false);
  const panelId = useId();

  return (
    <nav className={styles.mobileMenu} aria-label="Mobile primary navigation">
      <button
        type="button"
        className={styles.mobileMenuToggle}
        aria-expanded={open}
        aria-controls={panelId}
        onClick={() => setOpen((current) => !current)}
      >
        <span aria-hidden="true">{open ? "×" : "☰"}</span>
        {open ? "Close menu" : "Open menu"}
      </button>

      {open ? (
        <div className={styles.mobileMenuPanel} id={panelId}>
          {groups.map((item) => (
            <Link
              key={item.title}
              className={styles.mobileMenuLink}
              href={item.href}
              onClick={() => setOpen(false)}
            >
              <span>{item.title}</span>
              <span className={styles.menuLinkDescription}>{item.description}</span>
            </Link>
          ))}
        </div>
      ) : null}
    </nav>
  );
}
