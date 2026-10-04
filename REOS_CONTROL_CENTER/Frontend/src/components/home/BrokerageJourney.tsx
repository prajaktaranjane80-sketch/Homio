import styles from "./BrokerageJourney.module.css";

const steps = [
  {
    number: "01",
    title: "Discover",
    description: "Find the property, project or market that fits your intent.",
  },
  {
    number: "02",
    title: "Enquire",
    description: "Send your interest directly into the HOMIO journey.",
  },
  {
    number: "03",
    title: "Visit",
    description: "Move from digital discovery toward the right property visit.",
  },
  {
    number: "04",
    title: "Deal",
    description: "Continue through a structured HOMIO brokerage process.",
  },
];

export default function BrokerageJourney() {
  return (
    <div className={styles.panel}>
      <div className={styles.header}>
        <span>THE HOMIO JOURNEY</span>
        <small>DISCOVERY → BROKERAGE</small>
      </div>

      <div className={styles.steps}>
        {steps.map((step, index) => (
          <div key={step.number} className={styles.step}>
            <div className={styles.number}>{step.number}</div>

            <div className={styles.content}>
              <h3>{step.title}</h3>
              <p>{step.description}</p>
            </div>

            {index < steps.length - 1 && <div className={styles.connector} />}
          </div>
        ))}
      </div>
    </div>
  );
}
