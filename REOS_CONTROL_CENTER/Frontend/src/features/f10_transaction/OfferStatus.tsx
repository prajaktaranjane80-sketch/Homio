import {
  OFFER_STATUS_META,
  TONE_CLASS_KEY,
} from "./transaction.constants";
import type { OfferStatusCode } from "./transaction.types";
import styles from "./TransactionWorkspace.module.css";

type Props = Readonly<{
  status: OfferStatusCode;
}>;

export default function OfferStatus({ status }: Props) {
  const meta = OFFER_STATUS_META[status];

  return (
    <span
      className={`${styles.statusBadge} ${styles[TONE_CLASS_KEY[meta.tone]]}`}
    >
      <span className={styles.statusDot} aria-hidden="true" />
      {meta.label}
    </span>
  );
}
