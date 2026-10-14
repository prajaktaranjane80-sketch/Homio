import Link from "next/link";
import styles from "./HomeServices.module.css";

const services = [
  {
    title: "Home Loans",
    description:
      "A preview of how financing information could sit alongside a property journey.",
    icon: "01",
  },
  {
    title: "Property Valuation",
    description:
      "A concept for presenting value context using location and property facts.",
    icon: "02",
  },
  {
    title: "Interiors",
    description:
      "A preview of support around furniture, renovation and interiors.",
    icon: "03",
  },
  {
    title: "Moving & Relocation",
    description:
      "A concept for helping consumers prepare for a move to a home or city.",
    icon: "04",
  },
  {
    title: "Property Management",
    description:
      "A preview of information for ongoing ownership and rental needs.",
    icon: "05",
  },
  {
    title: "Expert Support",
    description:
      "A concept for guiding consumers toward an appropriate next step.",
    icon: "06",
  },
];

export default function HomeServices() {
  return (
    <section id="services" className={styles.section}>
      <div className="homio-container">
        <div className={styles.header}>
          <div>
            <span className={styles.eyebrow}>HOMIO SERVICES</span>

            <h2>More than property discovery.</h2>

            <p>
              These cards demonstrate the intended service experience.
              Service-provider integrations, booking and fulfilment workflows
              are not active in this homepage preview.
            </p>
          </div>

          <span className={styles.viewAll} aria-disabled="true">
            Service experience preview
          </span>
        </div>

        <div className={styles.grid}>
          {services.map((service) => (
              <article
                key={service.title}
                className={styles.card}
              >
              <div className={styles.top}>
                <span className={styles.number}>{service.icon}</span>
                <span className={styles.arrow} aria-hidden="true">
                  ◇
                </span>
              </div>

              <h3>{service.title}</h3>
              <p>{service.description}</p>

              <span className={styles.explore}>
                Preview only · workflow not active
              </span>
            </article>
          ))}
        </div>

        <div className={styles.bottom}>
          <div className={styles.bottomIcon} aria-hidden="true">
            H
          </div>

          <div>
            <strong>One property journey, connected end to end.</strong>

            <p>
              The service cards are product concepts; they do not confirm
              provider availability or an active service-booking system.
            </p>
          </div>

          <Link href="/search" className={styles.bottomAction}>
            Continue property discovery
          </Link>
        </div>
      </div>
    </section>
  );
}
