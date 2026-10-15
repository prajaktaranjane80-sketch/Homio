import {
  TRANSACTION_STATUS_META,
  TONE_CLASS_KEY,
  formatDate,
} from "./transaction.constants";
import type { TransactionStatusCode } from "./transaction.types";
import styles from "./TransactionWorkspace.module.css";

type Props = Readonly<{
  status: TransactionStatusCode;
  updatedAt?: string;
  compact?: boolean;
}>;

export default function TransactionStatus({
  status,
  updatedAt,
  compact = false,
}: Props) {
  const meta = TRANSACTION_STATUS_META[status];

  return (
    <div className={styles.statusBlock}>
      <span
        className={`${styles.statusBadge} ${styles[TONE_CLASS_KEY[meta.tone]]}`}
      >
        <span className={styles.statusDot} aria-hidden="true" />
        {meta.label}
      </span>

      {!compact && updatedAt ? (
        <span className={styles.statusTimestamp}>
          Updated {formatDate(updatedAt)}
        </span>
      ) : null}
    </div>
  );
}
