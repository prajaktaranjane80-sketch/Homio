import {
  formatDate,
  humanizeCode,
} from "./transaction.constants";
import type {
  TransactionActionRequestHandler,
  TransactionRecord,
} from "./transaction.types";
import styles from "./TransactionWorkspace.module.css";

type Props = Readonly<{
  transaction: TransactionRecord;
  onActionRequest?: TransactionActionRequestHandler;
}>;

export default function DealOverview({
  transaction,
  onActionRequest,
}: Props) {
  const nextAction =
    transaction.nextActions.find((action) => action.state === "available") ??
    transaction.nextActions.find((action) => action.state === "pending");

  const canRequestAction =
    Boolean(nextAction) &&
    nextAction?.state === "available" &&
    Boolean(onActionRequest);

  return (
    <section className={`${styles.panel} ${styles.overviewPanel}`}>
      <div className={styles.overviewHeader}>
        <div>
          <p className={styles.eyebrow}>TRANSACTION SUMMARY</p>
          <h2 className={styles.panelTitle}>{transaction.title}</h2>
          <p className={styles.panelDescription}>
            Review the current position, then continue through the actions
            supplied for this transaction.
          </p>
        </div>

        <div className={styles.referenceBlock}>
          <span className={styles.miniLabel}>Transaction reference</span>
          <span className={styles.referenceValue}>
            {transaction.reference || "Reference not supplied"}
          </span>
        </div>
      </div>

      <div className={styles.summaryMetricGrid}>
        <div className={styles.summaryMetric}>
          <span className={styles.summaryMetricLabel}>Transaction ID</span>
          <span className={styles.summaryMetricValue}>
            {transaction.id}
          </span>
        </div>

        <div className={styles.summaryMetric}>
          <span className={styles.summaryMetricLabel}>Current stage</span>
          <span className={styles.summaryMetricValue}>
            {humanizeCode(transaction.status)}
          </span>
        </div>

        <div className={styles.summaryMetric}>
          <span className={styles.summaryMetricLabel}>Last updated</span>
          <span className={styles.summaryMetricValue}>
            {formatDate(transaction.updatedAt)}
          </span>
        </div>
      </div>

      {nextAction ? (
        <div className={styles.actionCard}>
          <div className={styles.actionCardMarker} aria-hidden="true">
            <svg viewBox="0 0 24 24" fill="none">
              <path
                d="M12 3.75L20 8.25V15.75L12 20.25L4 15.75V8.25L12 3.75Z"
                stroke="currentColor"
                strokeWidth="1.6"
                strokeLinejoin="round"
              />
              <path
                d="M8.5 12H15.5M12 8.5V15.5"
                stroke="currentColor"
                strokeWidth="1.6"
                strokeLinecap="round"
              />
            </svg>
          </div>

          <div className={styles.actionCardCopy}>
            <span className={styles.miniLabel}>NEXT ACTION PROVIDED</span>
            <h3 className={styles.actionCardTitle}>{nextAction.label}</h3>
            {nextAction.description ? (
              <p className={styles.actionCardDescription}>
                {nextAction.description}
              </p>
            ) : null}
            {nextAction.dueAt ? (
              <p className={styles.actionCardDescription}>
                Due {formatDate(nextAction.dueAt)}
              </p>
            ) : null}
          </div>

          <button
            type="button"
            className={styles.primaryButton}
            disabled={!canRequestAction}
            onClick={() => {
              if (nextAction.state === "available") {
                onActionRequest?.(nextAction);
              }
            }}
          >
            {nextAction.state === "available"
              ? "Continue"
              : nextAction.state === "pending"
                ? "In progress"
                : "Action unavailable"}
            <span aria-hidden="true">→</span>
          </button>
        </div>
      ) : (
        <div className={styles.inlineNotice} role="status">
          No next action has been supplied for this transaction.
        </div>
      )}

      <p className={styles.helperText}>
        Stage and action information are displayed as returned by the
        transaction service. This screen does not advance the transaction
        state by itself.
      </p>
    </section>
  );
}
