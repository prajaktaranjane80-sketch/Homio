import type { PropertyRecord } from "./property.types";
import styles from "./PropertyTrust.module.css";

type PropertyTrustProps = Readonly<{
  property: PropertyRecord;
}>;

export default function PropertyTrust({
  property,
}: PropertyTrustProps) {
  return (
    <section className={styles.section}>
      <div>
        <span className={styles.eyebrow}>TRUST & TRANSPARENCY</span>
        <h2>Know what HOMIO can verify.</h2>
        <p>
          Property information shown here is presented through the
          approved HOMIO experience layer. Verification status is
          never created by the frontend itself.
        </p>
      </div>

      <div className={styles.status}>
        <span className={property.verified ? styles.dotActive : styles.dot} />
        <div>
          <strong>
            {property.verified
              ? property.verificationLabel
              : "Verification information unavailable"}
          </strong>
          <span>
            Review authoritative details before making a final
            decision.
          </span>
        </div>
      </div>
    </section>
  );
}
