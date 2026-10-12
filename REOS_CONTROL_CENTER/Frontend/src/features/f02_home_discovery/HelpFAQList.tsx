import styles from "./HelpFAQList.module.css";

const questions = [
  {
    question: "How does a HOMIO enquiry work?",
    answer:
      "The intended journey connects a consumer's property interest with HOMIO brokerage. Enquiry submission and follow-up workflows are not connected in this homepage preview.",
  },
  {
    question: "Can I save properties without completing an enquiry?",
    answer:
      "Saving is planned as part of the My HOMIO experience. Persistent saved-property storage is not active in this preview.",
  },
  {
    question: "How does HOMIO handle property visits?",
    answer:
      "The intended journey provides context before a visit request. Real visit scheduling and confirmation are not connected in this preview.",
  },
  {
    question: "How can I contact HOMIO support?",
    answer:
      "A dedicated support-contact workflow is not available in this preview. Do not treat the sample help cards as an active support channel.",
  },
];

export default function HelpFAQList() {
  return (
    <div className={styles.panel}>
      <div className={styles.header}>
        <span>QUICK ANSWERS</span>
        <h3>Frequently asked</h3>
      </div>

      <div className={styles.questions}>
        {questions.map((item) => (
          <details key={item.question} className={styles.question}>
            <summary>
              <span>{item.question}</span>
              <span className={styles.expandIcon} aria-hidden="true">
                +
              </span>
            </summary>

            <p className={styles.answer}>{item.answer}</p>
          </details>
        ))}
      </div>

      <div className={styles.contact}>
        <div>
          <strong>Support workflow preview</strong>
          <p>
            The help content is informational only; no support request is
            submitted from this card.
          </p>
        </div>
      </div>
    </div>
  );
}
