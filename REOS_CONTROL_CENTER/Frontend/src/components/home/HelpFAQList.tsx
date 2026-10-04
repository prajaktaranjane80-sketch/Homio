import Link from "next/link";
import styles from "./HelpFAQList.module.css";

const questions = [
  "How does a HOMIO enquiry work?",
  "Can I save properties without completing an enquiry?",
  "How does HOMIO handle property visits?",
  "How can I contact HOMIO support?",
];

export default function HelpFAQList() {
  return (
    <div className={styles.panel}>
      <div className={styles.header}>
        <span>QUICK ANSWERS</span>
        <h3>Frequently asked</h3>
      </div>

      <div className={styles.questions}>
        {questions.map((question) => (
          <Link key={question} href="/help" className={styles.question}>
            <span>{question}</span>
            <span aria-hidden="true">+</span>
          </Link>
        ))}
      </div>

      <div className={styles.contact}>
        <div>
          <strong>Still need help?</strong>
          <p>Reach the HOMIO support experience.</p>
        </div>

        <Link href="/help/contact">Contact support</Link>
      </div>
    </div>
  );
}
