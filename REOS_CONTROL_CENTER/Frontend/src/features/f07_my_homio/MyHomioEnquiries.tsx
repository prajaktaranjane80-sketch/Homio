import styles from "./MyHomio.module.css";

const ENQUIRY_STAGES = [
  {
    number: "01",
    title: "Enquiry received",
    text: "The connected enquiry service reports the submitted request and its reference.",
  },
  {
    number: "02",
    title: "Response recorded",
    text: "The service supplies the response, timestamp and responsible party.",
  },
  {
    number: "03",
    title: "Next action",
    text: "A follow-up appears only when an authorized workflow reports it.",
  },
];

export default function MyHomioEnquiries() {
  return (
    <>
      <header className={styles.panelHeader}>
        <p className={styles.kicker}>ENQUIRY MANAGEMENT</p>

        <h2 className={styles.panelTitle}>Your enquiry pipeline</h2>

        <p className={styles.panelLead}>
          Review enquiry references, the reported response and the next
          action once the authorized enquiry service is connected.
        </p>
      </header>

      <div className={styles.featureCard}>
        <div className={styles.featureHead}>
          <h3 className={styles.featureTitle}>Enquiry activity feed</h3>
          <span className={styles.statusBadge}>Connection required</span>
        </div>

        <p className={styles.featureText}>
          No authoritative enquiry feed is available to this account
          workspace yet. Viewing a listing or opening an enquiry anchor
          is not treated as a submitted request.
        </p>

        <a className={styles.textLink} href="/search">
          Continue property discovery →
        </a>
      </div>

      <div className={styles.sectionHeading}>
        <div>
          <h3>Enquiry lifecycle</h3>
          <p>Reference workflow, not a report of your personal progress.</p>
        </div>
      </div>

      <div className={styles.journeyGrid}>
        {ENQUIRY_STAGES.map((stage) => (
          <article className={styles.journeyCard} key={stage.number}>
            <span className={styles.journeyNumber}>{stage.number}</span>
            <h4 className={styles.journeyTitle}>{stage.title}</h4>
            <p className={styles.journeyText}>{stage.text}</p>
          </article>
        ))}
      </div>
    </>
  );
}
