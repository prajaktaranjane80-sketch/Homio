import {
  COMMISSION_STATUS_META,
  formatCurrency,
  formatDate,
  TONE_CLASS_KEY,
} from "./transaction.constants";
import type { CommissionSummary } from "./transaction.types";
import styles from "./TransactionWorkspace.module.css";

type Props = Readonly<{
  commission?: CommissionSummary;
}>;

export default function CommissionStatus({ commission }: Props) {
  return (
    <section className={styles.panel} aria-labelledby="f10-commission-title">
      <div className={styles.panelHeader}>
        <div>
          <p className={styles.eyebrow}>PROFESSIONAL SETTLEMENT</p>
          <h2 className={styles.panelTitle} id="f10-commission-title">
            Commission status
          </h2>
        </div>
        {commission ? (
          <span
            className={`${styles.statusBadge} ${
              styles[TONE_CLASS_KEY[COMMISSION_STATUS_META[commission.status].tone]]
            }`}
          >
            <span className={styles.statusDot} aria-hidden="true" />
            {COMMISSION_STATUS_META[commission.status].label}
          </span>
        ) : (
          <span className={styles.statusBadge}>Not supplied</span>
        )}
      </div>

      {!commission ? (
        <p className={styles.emptyInline}>
          Commission details are not available in the supplied transaction
          record.
        </p>
      ) : (
        <>
          <div className={styles.commissionAmount}>
            <span className={styles.miniLabel}>Commission amount</span>
            <strong>
              {formatCurrency(commission.amount, commission.currency)}
            </strong>
          </div>

          <dl className={styles.detailList}>
            <div className={styles.detailRow}>
              <dt className={styles.detailTerm}>Basis</dt>
              <dd className={styles.detailValue}>
                {commission.basisLabel || "Not supplied"}
              </dd>
            </div>
            <div className={styles.detailRow}>
              <dt className={styles.detailTerm}>Payable date</dt>
              <dd className={styles.detailValue}>
                {formatDate(commission.payableAt)}
              </dd>
            </div>
          </dl>

          {commission.serviceNote ? (
            <p className={styles.inlineNotice}>{commission.serviceNote}</p>
          ) : null}
        </>
      )}

      <p className={styles.helperText}>
        Commission amounts, entitlement and settlement status must come from
        the authorized REOS source and be restricted to viewers permitted to
        see them.
      </p>
    </section>
  );
}
