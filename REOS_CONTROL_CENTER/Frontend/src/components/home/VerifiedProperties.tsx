import Link from "next/link";
import styles from "./VerifiedProperties.module.css";

const properties = [
  {
    title: "Palm View Residence",
    location: "Palm Jumeirah, Dubai",
    type: "4 Bed Villa",
    price: "AED 8.90M",
    image:
      "https://images.unsplash.com/photo-1600047509358-9dc75507daeb?auto=format&fit=crop&w=1400&q=85",
    href: "/property/palm-view-residence",
    signals: ["Property details", "Location", "Availability"],
  },
  {
    title: "Central Garden Residence",
    location: "Bukit Timah, Singapore",
    type: "3 Bed Residence",
    price: "SGD 3.40M",
    image:
      "https://images.unsplash.com/photo-1600566753190-17f0baa2a6c3?auto=format&fit=crop&w=1400&q=85",
    href: "/property/central-garden-residence",
    signals: ["Property details", "Project context", "Availability"],
  },
  {
    title: "Prime Metropolitan Home",
    location: "Shibuya, Tokyo",
    type: "2 Bed Apartment",
    price: "JPY 145M",
    image:
      "https://images.unsplash.com/photo-1600607687920-4e2a09cf159d?auto=format&fit=crop&w=1400&q=85",
    href: "/property/prime-metropolitan-home",
    signals: ["Property details", "Location", "Source context"],
  },
];

export default function VerifiedProperties() {
  return (
    <section className={styles.section}>
      <div className="homio-container">
        <div className={styles.top}>
          <div className={styles.heading}>
            <span className={styles.eyebrow}>HOMIO TRUST SIGNALS</span>

            <h2>Properties with stronger information signals.</h2>

            <p>
              HOMIO surfaces useful verification and source-context indicators
              so you can understand a property before taking the next step.
            </p>
          </div>

          <div className={styles.trustBox}>
            <span className={styles.trustIcon}>✓</span>

            <div>
              <strong>Trust is part of discovery.</strong>

              <p>
                Signals are shown alongside listings instead of hidden behind
                the enquiry flow.
              </p>
            </div>
          </div>
        </div>

        <div className={styles.grid}>
          {properties.map((property) => (
            <article key={property.title} className={styles.card}>
              <Link href={property.href} className={styles.imageLink}>
                <div className={styles.imageWrap}>
                  <img
                    src={property.image}
                    alt={property.title}
                    className={styles.image}
                    loading="lazy"
                  />

                  <span className={styles.verified}>
                    <span aria-hidden="true">✓</span>
                    HOMIO signal
                  </span>
                </div>
              </Link>

              <div className={styles.body}>
                <div className={styles.type}>{property.type}</div>

                <Link href={property.href} className={styles.title}>
                  {property.title}
                </Link>

                <p className={styles.location}>{property.location}</p>

                <div className={styles.signals}>
                  {property.signals.map((signal) => (
                    <span key={signal} className={styles.signal}>
                      <span aria-hidden="true">✓</span>
                      {signal}
                    </span>
                  ))}
                </div>

                <div className={styles.footer}>
                  <strong>{property.price}</strong>

                  <Link href={property.href} className={styles.action}>
                    Check property
                    <span aria-hidden="true">→</span>
                  </Link>
                </div>
              </div>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
