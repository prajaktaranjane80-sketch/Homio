
/* File: src/components/system/FeatureLockedState.tsx */
import Link from "next/link";

import styles from "./SharedSystem.module.css";

type Props = Readonly<{
  title: string;
  description: string;
  eyebrow?: string;
  actionLabel?: string;
  href?: string;
}>;

function isSafeInternalHref(href: string): boolean {
  return href.startsWith("/") && !href.startsWith("//");
}

export default function FeatureLockedState({
  title,
  description,
  eyebrow = "ACCESS CONTROL",
  actionLabel,
  href,
}: Props) {
  const safeHref = href && isSafeInternalHref(href) ? href : undefined;

  return (
    <section className={styles.systemPanel} role="note">
      <span className={styles.systemPanelIcon} aria-hidden="true">
        ◈
      </span>

      <div className={styles.systemPanelBody}>
        <span className={styles.systemEyebrow}>{eyebrow}</span>
        <h2 className={styles.systemTitle}>{title}</h2>
        <p className={styles.systemDescription}>{description}</p>

        {actionLabel && safeHref ? (
          <p className={styles.systemMeta}>
            <Link href={safeHref}>{actionLabel} →</Link>
          </p>
        ) : null}
      </div>
    </section>
  );
}
