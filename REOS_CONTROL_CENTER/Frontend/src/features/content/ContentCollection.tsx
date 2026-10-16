import Link from "next/link";

import styles from "./ContentExperience.module.css";
import type { ContentIndexProps } from "./ContentExperience.types";

export default function ContentCollection({
  title,
  description,
  items,
  emptyMessage = "No published items have been provided by the content source.",
}: ContentIndexProps) {
  return (
    <section className={styles.contentRoot}>
      <header className={styles.contentHeader}>
        <span className={styles.contentEyebrow}>HOMIO KNOWLEDGE</span>
        <h1 className={styles.contentTitle}>{title}</h1>
        <p className={styles.contentDescription}>{description}</p>
      </header>

      {items.length === 0 ? (
        <div className={styles.contentEmpty}>{emptyMessage}</div>
      ) : (
        <div className={styles.contentGrid}>
          {items.map((item) => (
            <Link className={styles.contentCard} href={item.href} key={item.id}>
              {item.category ? (
                <span className={styles.contentCardLabel}>{item.category}</span>
              ) : null}
              <h2 className={styles.contentCardTitle}>{item.title}</h2>
              <p className={styles.contentCardDescription}>{item.description}</p>
              <span className={styles.contentCardFooter}>
                Read more <span aria-hidden="true">↗</span>
              </span>
            </Link>
          ))}
        </div>
      )}
    </section>
  );
}
