import {
  FINANCIAL_STATUS_META,
  formatCurrency,
  formatDate,
  TONE_CLASS_KEY,
} from "./transaction.constants";
import type { TransactionFinancialSummary } from "./transaction.types";
import styles from "./TransactionWorkspace.module.css";

type Props = Readonly<{
  summary?: TransactionFinancialSummary;
}>;

export default function TransactionFinancialStatus({ summary }: Props) {
  if (!summary) {
    return (
      <section className={styles.panel}>
        <div className={styles.panelHeader}>
          <div>
            <p className={styles.eyebrow}>PAYMENTS & BALANCES</p>
            <h2 className={styles.panelTitle}>Financial status</h2>
          </div>
          <span className={styles.statusBadge}>Not supplied</span>
        </div>
        <p className={styles.emptyInline}>
          No financial summary has been supplied for this viewer.
        </p>
      </section>
    );
  }

  const meta = FINANCIAL_STATUS_META[summary.status];

  const amounts = [
    { label: "Total amount", value: summary.totalAmount },
    { label: "Paid to date", value: summary.paidToDate },
    { label: "Remaining balance", value: summary.balanceRemaining },
    { label: "Next payment", value: summary.nextPaymentAmount },
  ].filter((item) => item.value !== undefined);

  return (
    <section className={styles.panel} aria-labelledby="f10-financial-title">
      <div className={styles.panelHeader}>
        <div>
          <p className={styles.eyebrow}>PAYMENTS & BALANCES</p>
          <h2 className={styles.panelTitle} id="f10-financial-title">
            Financial status
          </h2>
        </div>
        <span
          className={`${styles.statusBadge} ${styles[TONE_CLASS_KEY[meta.tone]]}`}
        >
          <span className={styles.statusDot} aria-hidden="true" />
          {meta.label}
        </span>
      </div>

      {amounts.length > 0 ? (
        <dl className={styles.financialGrid}>
          {amounts.map((item) => (
            <div className={styles.financialItem} key={item.label}>
              <dt className={styles.financialLabel}>{item.label}</dt>
              <dd className={styles.financialValue}>
                {formatCurrency(item.value, summary.currency)}
              </dd>
            </div>
          ))}
        </dl>
      ) : (
        <p className={styles.emptyInline}>
          Amount details have not been supplied.
        </p>
      )}

      {summary.nextPaymentDueAt ? (
        <div className={styles.financialDue}>
          <span className={styles.financialDueLabel}>Next payment date</span>
          <strong>{formatDate(summary.nextPaymentDueAt)}</strong>
        </div>
      ) : null}

      {summary.serviceNote ? (
        <p className={styles.inlineNotice}>{summary.serviceNote}</p>
      ) : null}

      <p className={styles.helperText}>
        Amounts and payment state are presented as supplied. The UI does not
        calculate a balance, initiate a payment or confirm settlement.
      </p>
    </section>
  );
}
