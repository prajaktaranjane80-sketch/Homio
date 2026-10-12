import type { PropertyRecord } from "./property.types";
import styles from "./PropertyTrust.module.css";

type PropertyTrustProps = Readonly<{
  property: PropertyRecord;
}>;

export default function PropertyTrust({
  property,
}: PropertyTrustProps) {
  return (
    <section
      className={styles.section}
      aria-labelledby="property-trust-heading"
    >
      <div>
        <span className={styles.eyebrow}>
          TRUST & TRANSPARENCY
        </span>

        <h2 id="property-trust-heading">
          Know what HOMIO can verify.
        </h2>

        <p>
          Verification must come from an approved, authoritative source.
          The frontend does not independently verify ownership, pricing,
          availability or property claims.
        </p>
      </div>

      <div
        className={styles.status}
        role="note"
        aria-label="Property verification status"
      >
        <span
          className={
            property.verified ? styles.dotActive : styles.dot
          }
          aria-hidden="true"
        />

        <div>
          <strong>
            {property.verificationLabel ||
              (property.verified
                ? "Verification status supplied by source"
                : "Not verified — experience preview")}
          </strong>

          <span>
            {property.verified
              ? "This status is supplied by the connected data source. Review the underlying evidence before making a commitment."
              : "This sample record has not been verified. Do not treat its details as confirmed inventory."}
          </span>
        </div>
      </div>
    </section>
  );
}
