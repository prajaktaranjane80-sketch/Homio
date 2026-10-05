import styles from "./SearchErrorState.module.css";

type SearchErrorStateProps = Readonly<{
  title?: string;
  description?: string;
  onRetry?: () => void;
}>;

export default function SearchErrorState({
  title = "Search is temporarily unavailable.",
  description = "HOMIO could not complete this search. Please try again without changing your search criteria.",
  onRetry,
}: SearchErrorStateProps) {
  return (
    <section className={styles.state} aria-live="assertive">
      <div className={styles.icon} aria-hidden="true">
        !
      </div>

      <span className={styles.eyebrow}>SEARCH ERROR</span>

      <h2>{title}</h2>

      <p>{description}</p>

      {onRetry ? (
        <button type="button" className={styles.button} onClick={onRetry}>
          Try again
        </button>
      ) : null}
    </section>
  );
}
