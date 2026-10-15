import {
  DOCUMENT_STATUS_META,
  formatDate,
  TONE_CLASS_KEY,
} from "./transaction.constants";
import type {
  TransactionActionRequestHandler,
  TransactionDocument,
} from "./transaction.types";
import styles from "./TransactionWorkspace.module.css";

type Props = Readonly<{
  documents: readonly TransactionDocument[];
  onActionRequest?: TransactionActionRequestHandler;
}>;

export default function DocumentChecklist({
  documents,
  onActionRequest,
}: Props) {
  const requiredCount = documents.filter((item) => item.required).length;
  const verifiedCount = documents.filter(
    (item) => item.required && item.status === "verified",
  ).length;

  return (
    <section className={styles.panel} aria-labelledby="f10-documents-title">
      <div className={styles.panelHeader}>
        <div>
          <p className={styles.eyebrow}>TRANSACTION RECORDS</p>
          <h2 className={styles.panelTitle} id="f10-documents-title">
            Document checklist
          </h2>
          <p className={styles.panelDescription}>
            Required items and verification states supplied for this
            transaction.
          </p>
        </div>
        <span className={styles.countPill}>{documents.length}</span>
      </div>

      <div className={styles.documentSummary}>
        <div className={styles.documentSummaryIcon} aria-hidden="true">
          <svg viewBox="0 0 24 24" fill="none">
            <path
              d="M7 3.75H14L19 8.75V20.25H7C5.9 20.25 5 19.35 5 18.25V5.75C5 4.65 5.9 3.75 7 3.75Z"
              stroke="currentColor"
              strokeWidth="1.6"
              strokeLinejoin="round"
            />
            <path
              d="M14 3.75V9H19M8.5 13H15.5M8.5 16.5H14"
              stroke="currentColor"
              strokeWidth="1.6"
              strokeLinecap="round"
            />
          </svg>
        </div>
        <div>
          <strong>
            {verifiedCount} of {requiredCount} required items verified
          </strong>
          <p>
            This count reflects the statuses supplied by the transaction
            service; it is not a legal or completion decision.
          </p>
        </div>
      </div>

      {documents.length === 0 ? (
        <p className={styles.emptyInline}>
          No document requirements have been supplied.
        </p>
      ) : (
        <ul className={styles.documentList}>
          {documents.map((document) => {
            const meta = DOCUMENT_STATUS_META[document.status];
            const action = document.action;
            const canRequestAction =
              action?.state === "available" && Boolean(onActionRequest);

            return (
              <li className={styles.documentRow} key={document.id}>
                <span className={styles.documentIcon} aria-hidden="true">
                  DOC
                </span>

                <div className={styles.documentCopy}>
                  <div className={styles.documentTitleRow}>
                    <h3 className={styles.documentName}>{document.name}</h3>
                    {document.required ? (
                      <span className={styles.requiredTag}>Required</span>
                    ) : (
                      <span className={styles.optionalTag}>Optional</span>
                    )}
                  </div>

                  {document.description ? (
                    <p className={styles.itemDescription}>
                      {document.description}
                    </p>
                  ) : null}

                  <div className={styles.documentMeta}>
                    <span
                      className={`${styles.statusBadge} ${styles[TONE_CLASS_KEY[meta.tone]]}`}
                    >
                      <span className={styles.statusDot} aria-hidden="true" />
                      {meta.label}
                    </span>
                    {document.dueAt ? (
                      <span>Due {formatDate(document.dueAt)}</span>
                    ) : null}
                    {document.updatedAt ? (
                      <span>Updated {formatDate(document.updatedAt)}</span>
                    ) : null}
                  </div>

                  {action ? (
                    <button
                      type="button"
                      className={styles.textButton}
                      disabled={!canRequestAction}
                      onClick={() => {
                        if (action.state === "available") {
                          onActionRequest?.(action);
                        }
                      }}
                    >
                      {action.label}
                      <span aria-hidden="true"> →</span>
                    </button>
                  ) : null}
                </div>
              </li>
            );
          })}
        </ul>
      )}

      <p className={styles.helperText}>
        Upload, review and verification actions are not simulated in the
        frontend. They must be handled by authorized document services.
      </p>
    </section>
  );
}
