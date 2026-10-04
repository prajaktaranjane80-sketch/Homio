import Link from "next/link";
import styles from "./PostPropertySection.module.css";

const benefits = [
  {
    title: "Reach the right audience",
    description:
      "Present your property through HOMIO discovery across relevant locations and property categories.",
  },
  {
    title: "Structured property information",
    description:
      "Give buyers and renters the context they need before they enquire.",
  },
  {
    title: "HOMIO brokerage pathway",
    description:
      "Move genuine interest into a structured enquiry and brokerage journey.",
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
              Share your property with HOMIO and put it in front of people
              actively exploring homes, investment opportunities and commercial
              real estate.
            </p>

            <div className={styles.actions}>
              <Link href="/pro/inventory" className={styles.primary}>
                List a property
                <span aria-hidden="true">↗</span>
              </Link>

              <Link href="/pro" className={styles.secondary}>
                Learn about HOMIO Pro
              </Link>
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
            &nbsp; Bring suitable inventory into the HOMIO ecosystem.
          </span>

          <Link href="/pro/inventory">Open property submission</Link>
        </div>
      </div>
    </section>
  );
}
