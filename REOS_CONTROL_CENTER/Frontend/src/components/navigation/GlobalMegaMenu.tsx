import Link from "next/link";
import type { ReactNode } from "react";

import styles from "./GlobalMenus.module.css";

export type GlobalMenuItem = Readonly<{
  href: string;
  title: string;
  description: string;
  icon?: ReactNode;
  status?: string;
}>;

type Props = Readonly<{
  eyebrow?: string;
  title: string;
  description: string;
  items: readonly GlobalMenuItem[];
}>;

export default function GlobalMegaMenu({
  eyebrow = "HOMIO GLOBAL",
  title,
  description,
  items,
}: Props) {
  return (
    <nav className={styles.menuRoot} aria-label={title}>
      <div className={styles.menuPanel}>
        <div className={styles.menuIntro}>
          <span className={styles.menuEyebrow}>{eyebrow}</span>
          <h2 className={styles.menuTitle}>{title}</h2>
          <p className={styles.menuDescription}>{description}</p>
        </div>

        <div className={styles.menuGrid}>
          {items.map((item) => (
            <Link key={`${item.href}-${item.title}`} href={item.href} className={styles.menuLink}>
              <span className={styles.menuLinkIcon} aria-hidden="true">
                {item.icon ?? "↗"}
              </span>
              <span className={styles.menuLinkBody}>
                <span className={styles.menuLinkTitle}>{item.title}</span>
                <span className={styles.menuLinkDescription}>{item.description}</span>
                {item.status ? <span className={styles.menuLinkStatus}>{item.status}</span> : null}
              </span>
            </Link>
          ))}
        </div>
      </div>
    </nav>
  );
}
