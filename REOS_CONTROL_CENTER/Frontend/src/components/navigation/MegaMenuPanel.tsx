
import Link from "next/link";

import styles from "./MegaMenu.module.css";
import type { MegaMenuItem } from "./mega-menu.types";

type Props = Readonly<{
  title: string;
  eyebrow?: string;
  description: string;
  items: readonly MegaMenuItem[];
}>;

function validInternalHref(href: string): boolean {
  return href.startsWith("/") && !href.startsWith("//");
}

export default function MegaMenuPanel({
  title,
  eyebrow = "HOMIO",
  description,
  items,
}: Props) {
  return (
    <section className={styles.menuPanel} aria-label={title}>
      <span className={styles.menuEyebrow}>{eyebrow}</span>
      <h2 className={styles.menuTitle}>{title}</h2>
      <p className={styles.menuDescription}>{description}</p>

      <div className={styles.menuItems}>
        {items.map((item) => {
          const content = (
            <>
              <span className={styles.menuItemContent}>
                <span className={styles.menuItemTitle}>
                  {item.label}
                </span>
                <span className={styles.menuItemDescription}>
                  {item.description}
                </span>
              </span>

              {item.badge ? (
                <span className={styles.menuItemBadge}>{item.badge}</span>
              ) : item.href && !item.disabled ? (
                <span className={styles.menuArrow} aria-hidden="true">
                  ↗
                </span>
              ) : null}
            </>
          );

          if (
            item.href &&
            validInternalHref(item.href) &&
            !item.disabled
          ) {
            return (
              <Link
                className={styles.menuItem}
                href={item.href}
                key={item.label}
              >
                {content}
              </Link>
            );
          }

          return (
            <div
              className={`${styles.menuItem} ${styles.menuItemDisabled}`}
              key={item.label}
              aria-disabled="true"
            >
              {content}
            </div>
          );
        })}
      </div>
    </section>
  );
}
