import styles from "./MyHomio.module.css";

const JOURNEY = [
  {
    number: "01",
    title: "Discover",
    detail:
      "Explore locations, properties and projects; save options worth revisiting.",
  },
  {
    number: "02",
    title: "Enquire",
    detail:
      "Submit a request through an enabled enquiry workflow and retain its source reference.",
  },
  {
    number: "03",
    title: "Coordinate",
    detail:
      "Follow proposed times, confirmed visits and actual responses when recorded by their services.",
  },
  {
    number: "04",
    title: "Evaluate",
    detail:
      "Compare supplied facts and review verified project or property documents.",
  },
  {
    number: "05",
    title: "Progress",
    detail:
      "View transaction or brokerage milestones only when the responsible workflow reports them.",
  },
];

export default function MyHomioBrokerageJourney() {
  return (
    <>
      <header className={styles.panelHeader}>
        <p className={styles.kicker}>PROPERTY JOURNEY</p>

        <h2 className={styles.panelTitle}>From discovery to decision</h2>

        <p className={styles.panelLead}>
          My HOMIO is designed to keep the journey legible—from the first
          shortlist to an informed decision—without suggesting a transaction
          has moved forward unless an authorized event confirms it.
        </p>
      </header>

      <div className={styles.featureCard}>
        <div className={styles.featureHead}>
          <h3 className={styles.featureTitle}>Personal journey feed</h3>
          <span className={styles.statusBadge}>Workflow connection required</span>
        </div>

        <p className={styles.featureText}>
          A user-specific brokerage timeline is not yet supplied to this
          account view. No step is marked completed, in progress or delayed
          on the basis of browsing alone.
        </p>
      </div>

      <div className={styles.sectionHeading}>
        <div>
          <h3>Journey framework</h3>
          <p>Reference stages only; this is not a live transaction timeline.</p>
        </div>
      </div>

      <div className={styles.journeyGrid}>
        {JOURNEY.map((stage) => (
          <article className={styles.journeyCard} key={stage.number}>
            <span className={styles.journeyNumber}>{stage.number}</span>
            <h4 className={styles.journeyTitle}>{stage.title}</h4>
            <p className={styles.journeyText}>{stage.detail}</p>
          </article>
        ))}
      </div>

      <div className={styles.sectionHeading}>
        <div>
          <h3>What makes a milestone valid?</h3>
        </div>
      </div>

      <div className={styles.contentGrid}>
        <article className={styles.featureCard}>
          <h3 className={styles.featureTitle}>Source reference</h3>
          <p className={styles.featureText}>
            Each milestone needs a real source record or authorized
            workflow event before appearing on a personal timeline.
          </p>
        </article>

        <article className={styles.featureCard}>
          <h3 className={styles.featureTitle}>Clear status</h3>
          <p className={styles.featureText}>
            A request, proposal, confirmation and completion are distinct
            states; the interface must not treat them as interchangeable.
          </p>
        </article>
      </div>
    </>
  );
}
