import OfferStatus from "./OfferStatus";
import {
  formatCurrency,
  formatDate,
} from "./transaction.constants";
import type { OfferDetails } from "./transaction.types";
import styles from "./TransactionWorkspace.module.css";

type Props = Readonly<{
  offer?: OfferDetails;
}>;

export default function OfferSummary({ offer }: Props) {
  return (
    <section className={styles.panel} aria-labelledby="f10-offer-title">
      <div className={styles.panelHeader}>
        <div>
          <p className={styles.eyebrow}>COMMERCIAL TERMS</p>
          <h2 className={styles.panelTitle} id="f10-offer-title">
            Offer summary
          </h2>
        </div>
        {offer ? (
          <OfferStatus status={offer.status} />
        ) : (
          <span className={styles.statusBadge}>Not supplied</span>
        )}
      </div>

      {!offer ? (
        <p className={styles.emptyInline}>
          No offer details have been supplied for this transaction.
        </p>
      ) : (
        <>
          <div className={styles.offerAmountPanel}>
            <span className={styles.offerAmountLabel}>Offer amount</span>
            <strong className={styles.offerAmountValue}>
              {formatCurrency(offer.amount, offer.currency)}
            </strong>
            <span className={styles.offerAmountCaption}>
              As reported by the transaction service
            </span>
          </div>

          <dl className={styles.detailList}>
            <div className={styles.detailRow}>
              <dt className={styles.detailTerm}>Submitted</dt>
              <dd className={styles.detailValue}>
                {formatDate(offer.submittedAt)}
              </dd>
            </div>
            <div className={styles.detailRow}>
              <dt className={styles.detailTerm}>Offer expiry</dt>
              <dd className={styles.detailValue}>
                {formatDate(offer.expiresAt)}
              </dd>
            </div>
          </dl>

          {offer.terms && offer.terms.length > 0 ? (
            <div className={styles.offerTerms}>
              <h3 className={styles.subheading}>Supplied terms</h3>
              <dl className={styles.detailList}>
                {offer.terms.map((term, index) => (
                  <div
                    className={styles.detailRow}
                    key={`${term.label}-${index}`}
                  >
                    <dt className={styles.detailTerm}>{term.label}</dt>
                    <dd className={styles.detailValue}>{term.value}</dd>
                  </div>
                ))}
              </dl>
            </div>
          ) : null}

          {offer.serviceNote ? (
            <p className={styles.inlineNotice}>{offer.serviceNote}</p>
          ) : null}
        </>
      )}
    </section>
  );
}
