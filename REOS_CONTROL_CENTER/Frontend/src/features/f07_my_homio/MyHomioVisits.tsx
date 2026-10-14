import styles from "./MyHomio.module.css";

const VISIT_STAGES = [
  {
    number: "01",
    title: "Request",
    text: "A visit request must be recorded by the connected scheduling service.",
  },
  {
    number: "02",
    title: "Proposed",
    text: "A suggested time must be returned by the responsible party.",
  },
  {
    number: "03",
    title: "Confirmed",
    text: "An appointment is confirmed only when the source explicitly confirms it.",
  },
  {
    number: "04",
    title: "Completed",
    text: "Completion is shown only when the authorized workflow reports it.",
  },
];

export default function MyHomioVisits() {
  return (
    <>
      <header className={styles.panelHeader}>
        <p className={styles.kicker}>VISIT COORDINATION</p>

        <h2 className={styles.panelTitle}>Visits & appointments</h2>

        <p className={styles.panelLead}>
          Keep proposed times, confirmed appointments and visit outcomes
          together when the authorized scheduling service is connected.
        </p>
      </header>

      <div className={styles.featureCard}>
        <div className={styles.featureHead}>
          <h3 className={styles.featureTitle}>Your appointment calendar</h3>
          <span className={styles.statusBadge}>No visit feed</span>
        </div>

        <p className={styles.featureText}>
          This account view has no connected visit records. There are no
          appointments to display or cancel from this screen. A “Schedule
          visit” link on a property page does not confirm a visit.
        </p>

        <a className={styles.textLink} href="/search">
          Return to property discovery →
        </a>
      </div>

      <div className={styles.sectionHeading}>
        <div>
          <h3>Appointment status definitions</h3>
          <p>These define the workflow; none is a current user status.</p>
        </div>
      </div>

      <div className={styles.journeyGrid}>
        {VISIT_STAGES.map((stage) => (
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
