import Link from "next/link";
import styles from "./HelpSupport.module.css";

const helpItems = [
  {
    title: "How HOMIO works",
    description: "Understand discovery, enquiry, visits and the brokerage journey.",
    href: "/help/how-homio-works",
  },
  {
    title: "Buying & renting",
    description: "Get practical answers before making a property decision.",
    href: "/help/buying-renting",
  },
  {
    title: "Using HOMIO AI",
    description: "Learn how AI can refine searches and explain property context.",
    href: "/help/homio-ai",
  },
  {
    title: "Account & saved items",
    description: "Manage saved properties, searches and your HOMIO journey.",
    href: "/help/account",
  },
];

const faqs = [
  "How does a HOMIO enquiry work?",
  "Can I save properties without completing an enquiry?",
  "How does HOMIO handle property visits?",
  "How can I contact HOMIO support?",
];

export default function HelpSupport() {
  return (
    <section id="help" className={styles.section}>
      <div className="homio-container">
        <div className={styles.header}>
          <div>
            <span className={styles.eyebrow}>HELP & SUPPORT</span>

            <h2>Need help finding your way?</h2>

            <p>
              Get practical guidance about using HOMIO, managing your journey
              and taking the next step.
            </p>
          </div>

          <Link href="/help" className={styles.viewAll}>
            Visit Help Center
            <span aria-hidden="true">↗</span>
          </Link>
        </div>

        <div className={styles.layout}>
          <div className={styles.helpGrid}>
            {helpItems.map((item) => (
              <Link key={item.title} href={item.href} className={styles.card}>
                <span className={styles.cardIcon} aria-hidden="true">
                  ?
                </span>

                <h3>{item.title}</h3>

                <p>{item.description}</p>

                <span className={styles.cardLink}>
                  Learn more
                  <span aria-hidden="true">→</span>
                </span>
              </Link>
            ))}
          </div>

          <div className={styles.faq}>
            <div className={styles.faqHeader}>
              <span className={styles.faqEyebrow}>QUICK ANSWERS</span>
              <h3>Frequently asked</h3>
            </div>

            <div className={styles.questions}>
              {faqs.map((faq) => (
                <Link key={faq} href="/help" className={styles.question}>
                  <span>{faq}</span>
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
        </div>
      </div>
    </section>
  );
}
