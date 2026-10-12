import styles from "./PropertyDisclosure.module.css";

type PropertyDisclosureProps = Readonly<{
  verified: boolean;
  verificationLabel: string;
}>;

export default function PropertyDisclosure({
  verified,
  verificationLabel,
}: PropertyDisclosureProps) {
  const statusLabel =
    verificationLabel ||
    (verified
      ? "Verification status supplied by source"
      : "Not verified — experience preview");

  return (
    <section
      className={styles.section}
      aria-labelledby="property-disclosure-heading"
    >
      <div className={styles.header}>
        <span className={styles.eyebrow}>
          IMPORTANT INFORMATION
        </span>

        <h2 id="property-disclosure-heading">
          Transparent property information.
        </h2>
      </div>

      <div className={styles.cards}>
        <article className={styles.card}>
          <span className={styles.icon} aria-hidden="true">
            i
          </span>

          <div>
            <strong>{statusLabel}</strong>

            <p>
              {verified
                ? "Verification status is supplied by the connected data source; it is not created by the frontend."
                : "This property experience is a preview. No authoritative verification has been established by this page."}
            </p>
          </div>
        </article>

        <article className={styles.card}>
          <span className={styles.icon} aria-hidden="true">
            i
          </span>

          <div>
            <strong>Pricing and availability</strong>

            <p>
              Displayed values may be illustrative. Price, ownership,
              availability, possession, dimensions and other details
              must be confirmed through authoritative data before
              a decision or commitment.
            </p>
          </div>
        </article>
      </div>
    </section>
  );
}
