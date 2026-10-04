import styles from "./PropertySubmissionBenefits.module.css";

const benefits = [
  {
    title: "Reach the right audience",
    description:
      "Present suitable property inventory through HOMIO discovery.",
  },
  {
    title: "Structured information",
    description:
      "Give buyers and renters the context they need before enquiry.",
  },
  {
    title: "Brokerage pathway",
    description:
      "Move genuine interest into a structured HOMIO enquiry journey.",
  },
];

export default function PropertySubmissionBenefits() {
  return (
    <div className={styles.grid}>
      {benefits.map((benefit, index) => (
        <div key={benefit.title} className={styles.item}>
          <span>{String(index + 1).padStart(2, "0")}</span>

          <div>
            <h3>{benefit.title}</h3>
            <p>{benefit.description}</p>
          </div>
        </div>
      ))}
    </div>
  );
}
