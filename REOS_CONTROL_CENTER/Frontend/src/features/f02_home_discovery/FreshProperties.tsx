import Link from "next/link";
import styles from "./FreshProperties.module.css";

const properties = [
  {
    title: "Skyline Residence",
    location: "Dubai Marina, Dubai",
    type: "3 Bed Apartment",
    price: "AED 3.25M",
    meta: "1,985 sq.ft",
    href: "/property/skyline-residence",
    image:
      "https://images.unsplash.com/photo-1600585152915-d208bec867a1?auto=format&fit=crop&w=1400&q=85",
  },
  {
    title: "Central Park Residence",
    location: "Downtown Dubai",
    type: "2 Bed Apartment",
    price: "AED 2.10M",
    meta: "1,240 sq.ft",
    href: "/property/central-park-residence",
    image:
      "https://images.unsplash.com/photo-1600607688969-a5bfcd646154?auto=format&fit=crop&w=1400&q=85",
  },
  {
    title: "Harbour View Home",
    location: "Singapore",
    type: "3 Bed Residence",
    price: "SGD 2.85M",
    meta: "1,650 sq.ft",
    href: "/property/harbour-view-home",
    image:
      "https://images.unsplash.com/photo-1600210492486-724fe5c67fb0?auto=format&fit=crop&w=1400&q=85",
  },
];

export default function FreshProperties() {
  return (
    <section className={styles.section}>
      <div className="homio-container">
        <div className={styles.header}>
          <div>
            <span className={styles.eyebrow}>FRESH PROPERTIES</span>

            <h2>New inventory worth a closer look.</h2>

            <p>
              Freshly surfaced opportunities presented with the essential
              details you need before starting a HOMIO enquiry.
            </p>
          </div>

          <Link href="/search?collection=fresh" className={styles.viewAll}>
            See fresh properties
            <span aria-hidden="true">↗</span>
          </Link>
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

                  <span className={styles.freshBadge}>Fresh</span>
                </div>
              </Link>

              <div className={styles.body}>
                <div className={styles.typeRow}>
                  <span>{property.type}</span>

                  <button
                    type="button"
                    className={styles.save}
                    aria-label={`Save ${property.title}`}
                  >
                    ♡
                  </button>
                </div>

                <Link href={property.href} className={styles.title}>
                  {property.title}
                </Link>

                <p className={styles.location}>{property.location}</p>

                <div className={styles.meta}>
                  <span>{property.meta}</span>
                  <span className={styles.dot}>•</span>
                  <span>Ready to explore</span>
                </div>

                <div className={styles.bottom}>
                  <strong>{property.price}</strong>

                  <Link href={property.href} className={styles.details}>
                    View property
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
