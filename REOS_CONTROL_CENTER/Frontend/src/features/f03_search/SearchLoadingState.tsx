import styles from "./SearchLoadingState.module.css";

type SearchLoadingStateProps = Readonly<{
  count?: number;
}>;

export default function SearchLoadingState({
  count = 6,
}: SearchLoadingStateProps) {
  return (
    <div
      className={styles.grid}
      aria-label="Loading search results"
      aria-busy="true"
    >
      {Array.from({ length: count }, (_, index) => (
        <div key={index} className={styles.card}>
          <div className={`${styles.block} ${styles.image}`} />
          <div className={styles.body}>
            <div className={`${styles.block} ${styles.short}`} />
            <div className={`${styles.block} ${styles.title}`} />
            <div className={`${styles.block} ${styles.line}`} />
            <div className={`${styles.block} ${styles.lineSmall}`} />
            <div className={styles.row}>
              <div className={`${styles.block} ${styles.price}`} />
              <div className={`${styles.block} ${styles.action}`} />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
