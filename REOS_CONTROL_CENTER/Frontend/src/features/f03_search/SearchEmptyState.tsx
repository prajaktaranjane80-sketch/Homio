import Link from "next/link";
import styles from "./SearchEmptyState.module.css";

type SearchEmptyStateProps = Readonly<{
  title?: string;
  description?: string;
  onReset?: () => void;
}>;

export default function SearchEmptyState({
  title = "No properties match your search.",
  description = "Try widening the location or removing a few filters to discover more HOMIO inventory.",
  onReset,
}: SearchEmptyStateProps) {
  return (
    <section className={styles.state} aria-label="No search results">
      <div className={styles.icon} aria-hidden="true">
        H
      </div>

      <span className={styles.eyebrow}>NO MATCHES</span>

      <h2>{title}</h2>

      <p>{description}</p>

      <div className={styles.actions}>
        {onReset ? (
          <button type="button" className={styles.primary} onClick={onReset}>
            Clear filters
          </button>
        ) : null}

        <Link href="/" className={styles.secondary}>
          Back to HOMIO
        </Link>
      </div>
    </section>
  );
}
