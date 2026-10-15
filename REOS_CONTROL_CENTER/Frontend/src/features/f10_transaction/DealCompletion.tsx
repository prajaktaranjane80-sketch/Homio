import {
  COMPLETION_STATUS_META,
  TONE_CLASS_KEY,
  formatDate,
} from "./transaction.constants";
import type { DealCompletionSummary } from "./transaction.types";
import styles from "./TransactionWorkspace.module.css";

type Props = Readonly<{
  completion?: DealCompletionSummary;
}>;

export default function DealCompletion({ completion }: Props) {
  if (!completion) {
    return (
      <section className={styles.panel}>
        <div className={styles.panelHeader}>
          <div>
            <p className={styles.eyebrow}>FINALIZATION</p>
            <h2 className={styles.panelTitle}>Deal completion</h2>
          </div>
          <span className={styles.statusBadge}>Not supplied</span>
        </div>
        <p className={styles.emptyInline}>
          Completion requirements have not been supplied for this transaction.
        </p>
      </section>
    );
  }

  const meta = COMPLETION_STATUS_META[completion.status];

  return (
    <section className={styles.panel} aria-labelledby="f10-completion-title">
      <div className={styles.panelHeader}>
        <div>
          <p className={styles.eyebrow}>FINALIZATION</p>
          <h2 className={styles.panelTitle} id="f10-completion-title">
            Deal completion
          </h2>
        </div>
        <span
          className={`${styles.statusBadge} ${styles[TONE_CLASS_KEY[meta.tone]]}`}
        >
          <span className={styles.statusDot} aria-hidden="true" />
          {meta.label}
        </span>
      </div>

      {completion.status === "completed" && completion.completedAt ? (
        <div className={styles.completionBanner}>
          <span className={styles.completionCheck} aria-hidden="true">
            ✓
          </span>
          <div>
            <strong>Completion recorded</strong>
            <p>{formatDate(completion.completedAt)}</p>
          </div>
        </div>
      ) : (
        <p className={styles.panelDescription}>
          Completion is shown according to the supplied service state. This
          screen cannot finalize or certify a deal.
        </p>
      )}

      {completion.items.length > 0 ? (
        <ul className={styles.completionList}>
          {completion.items.map((item) => (
            <li key={item.id} className={styles.completionItem}>
              <span
                className={`${styles.completionItemIcon} ${
                  item.status === "completed"
                    ? styles.completionItemIconDone
                    : item.status === "blocked"
                      ? styles.completionItemIconBlocked
                      : ""
                }`}
                aria-hidden="true"
              >
                {item.status === "completed"
                  ? "✓"
                  : item.status === "blocked"
                    ? "!"
                    : "–"}
              </span>
              <span className={styles.completionItemLabel}>{item.label}</span>
              <span className={styles.completionItemState}>
                {item.status === "completed"
                  ? "Complete"
                  : item.status === "blocked"
                    ? "Blocked"
                    : "Pending"}
              </span>
            </li>
          ))}
        </ul>
      ) : (
        <p className={styles.emptyInline}>
          No completion checklist items have been supplied.
        </p>
      )}

      {completion.serviceNote ? (
        <p className={styles.inlineNotice}>{completion.serviceNote}</p>
      ) : null}
    </section>
  );
}
