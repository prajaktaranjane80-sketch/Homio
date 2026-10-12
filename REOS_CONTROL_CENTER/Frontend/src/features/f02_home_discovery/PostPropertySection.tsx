import styles from "./PostPropertySection.module.css";

const benefits = [
  {
    title: "Reach the right audience",
    description:
      "The intended experience presents a property to people exploring relevant locations and property categories.",
  },
  {
    title: "Structured property information",
    description:
      "The planned listing workflow captures the context buyers and renters need before enquiring.",
  },
  {
    title: "HOMIO brokerage pathway",
    description:
      "The intended journey connects genuine interest with a structured brokerage workflow.",
  },
];

export default function PostPropertySection() {
  return (
    <section id="post-property" className={styles.section}>
      <div className="homio-container">
        <div className={styles.shell}>
          <div className={styles.content}>
            <span className={styles.eyebrow}>LIST WITH HOMIO</span>

            <h2>
              Have a property to
              <br />
              bring to market?
            </h2>

            <p>
              This section previews the intended property-submission journey.
              Property submission, partner authentication and inventory
              creation are not connected in the current frontend preview.
            </p>

            <div className={styles.actions}>
              <span className={styles.primary} aria-disabled="true">
                Property submission preview only
              </span>

              <span className={styles.secondary} aria-disabled="true">
                HOMIO Pro workflow not active
              </span>
            </div>
          </div>

          <div className={styles.benefits}>
            {benefits.map((benefit, index) => (
              <div key={benefit.title} className={styles.benefit}>
                <span className={styles.number}>
                  {String(index + 1).padStart(2, "0")}
                </span>

                <div>
                  <h3>{benefit.title}</h3>
                  <p>{benefit.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className={styles.bottom}>
          <span>
            <strong>Owners, developers and authorised partners.</strong>
            &nbsp; Listing workflows must be connected before any inventory
            can be submitted.
          </span>

          <span aria-disabled="true">Submission not enabled</span>
        </div>
      </div>
    </section>
  );
}
