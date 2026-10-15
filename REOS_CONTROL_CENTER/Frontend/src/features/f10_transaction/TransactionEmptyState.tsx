import styles from "./TransactionWorkspace.module.css";

type Props = Readonly<{
  title?: string;
  description?: string;
}>;

export default function TransactionEmptyState({
  title = "No transaction details to display",
  description = "A verified transaction record has not been supplied to this view. Open this workspace through an authorized transaction entry point after the transaction service is connected.",
}: Props) {
  return (
    <main className={styles.emptyStatePage}>
      <section className={styles.emptyState} aria-labelledby="f10-empty-title">
        <div className={styles.emptyIcon} aria-hidden="true">
          <svg viewBox="0 0 48 48" fill="none">
            <rect
              x="10"
              y="5"
              width="28"
              height="38"
              rx="5"
              stroke="currentColor"
              strokeWidth="1.7"
            />
            <path
              d="M17 16H31M17 23H31M17 30H25"
              stroke="currentColor"
              strokeWidth="1.7"
              strokeLinecap="round"
            />
            <circle
              cx="34"
              cy="35"
              r="7"
              fill="currentColor"
              fillOpacity=".12"
              stroke="currentColor"
              strokeWidth="1.5"
            />
            <path
              d="M34 32V35.5M34 38H34.02"
              stroke="currentColor"
              strokeWidth="1.7"
              strokeLinecap="round"
            />
          </svg>
        </div>

        <p className={styles.eyebrow}>F10 · TRANSACTION WORKSPACE</p>
        <h1 id="f10-empty-title" className={styles.emptyTitle}>
          {title}
        </h1>
        <p className={styles.emptyDescription}>{description}</p>
        <p className={styles.emptyFootnote}>
          No sample deal, payment status or document approval is being presented
          as real transaction data.
        </p>
      </section>
    </main>
  );
}
