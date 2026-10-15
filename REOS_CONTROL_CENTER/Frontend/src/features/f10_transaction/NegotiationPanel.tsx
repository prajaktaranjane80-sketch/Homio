import {
  formatDate,
  humanizeCode,
} from "./transaction.constants";
import type {
  NegotiationEntry,
  TransactionActionRequestHandler,
} from "./transaction.types";
import styles from "./TransactionWorkspace.module.css";

type Props = Readonly<{
  entries: readonly NegotiationEntry[];
  onActionRequest?: TransactionActionRequestHandler;
}>;

export default function NegotiationPanel({
  entries,
  onActionRequest,
}: Props) {
  return (
    <section className={styles.panel} aria-labelledby="f10-negotiation-title">
      <div className={styles.panelHeader}>
        <div>
          <p className={styles.eyebrow}>DISCUSSION & DECISIONS</p>
          <h2 className={styles.panelTitle} id="f10-negotiation-title">
            Negotiation
          </h2>
          <p className={styles.panelDescription}>
            Entries returned by the transaction service.
          </p>
        </div>
        <span className={styles.countPill}>{entries.length}</span>
      </div>

      {entries.length === 0 ? (
        <p className={styles.emptyInline}>
          No negotiation entries have been supplied.
        </p>
      ) : (
        <ol className={styles.activityList}>
          {entries.map((entry) => {
            const action = entry.action;
            const actionEnabled =
              action?.state === "available" && Boolean(onActionRequest);

            return (
              <li className={styles.activityItem} key={entry.id}>
                <span className={styles.activityMarker} aria-hidden="true">
                  <span />
                </span>

                <div className={styles.activityBody}>
                  <div className={styles.activityTop}>
                    <h3 className={styles.itemTitle}>{entry.title}</h3>
                    <span className={styles.smallStatus}>
                      {humanizeCode(entry.status)}
                    </span>
                  </div>

                  {entry.summary ? (
                    <p className={styles.itemDescription}>{entry.summary}</p>
                  ) : null}

                  <div className={styles.activityMeta}>
                    {entry.actorLabel ? <span>{entry.actorLabel}</span> : null}
                    <span>{formatDate(entry.updatedAt)}</span>
                  </div>

                  {action ? (
                    <div className={styles.inlineActionRow}>
                      <span className={styles.actionDescription}>
                        {action.description || action.label}
                      </span>
                      <button
                        type="button"
                        className={styles.secondaryButton}
                        disabled={!actionEnabled}
                        onClick={() => {
                          if (action.state === "available") {
                            onActionRequest?.(action);
                          }
                        }}
                      >
                        {action.state === "available"
                          ? action.label
                          : action.state === "pending"
                            ? "In progress"
                            : action.state === "completed"
                              ? "Completed"
                              : "Unavailable"}
                      </button>
                    </div>
                  ) : null}
                </div>
              </li>
            );
          })}
        </ol>
      )}

      <p className={styles.helperText}>
        The interface does not create a counteroffer, approve a term or send a
        message. Those actions require an authorized service.
      </p>
    </section>
  );
}
