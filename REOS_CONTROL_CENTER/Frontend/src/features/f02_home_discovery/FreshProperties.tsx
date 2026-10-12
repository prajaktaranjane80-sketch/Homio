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
    <section className={styles.section} aria-labelledby="property-preview-heading">
      <div className="homio-container">
        <div className={styles.header}>
          <div>
            <span className={styles.eyebrow}>
              PROPERTY EXPERIENCE PREVIEWS
            </span>

            <h2 id="property-preview-heading">
              Property experiences worth exploring.
            </h2>

            <p>
              The listings below are static experience examples, not freshly
              published inventory. Prices, locations, areas and availability
              are illustrative and have not been verified as live listings.
            </p>
          </div>

          <Link href="/search?intent=buy" className={styles.viewAll}>
            Browse property search
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
                    alt={`Illustrative property image for ${property.title}`}
                    className={styles.image}
                    loading="lazy"
                  />

                  <span className={styles.freshBadge}>
                    Experience preview
                  </span>
                </div>
              </Link>

              <div className={styles.body}>
                <div className={styles.typeRow}>
                  <span>{property.type}</span>
                </div>

                <Link href={property.href} className={styles.title}>
                  {property.title}
                </Link>

                <p className={styles.location}>{property.location}</p>

                <div className={styles.meta}>
                  <span>{property.meta}</span>
                  <span className={styles.dot} aria-hidden="true">
                    •
                  </span>
                  <span>Illustrative details · not verified</span>
                </div>

                <div className={styles.bottom}>
                  <strong>{property.price}</strong>

                  <Link href={property.href} className={styles.details}>
                    View preview
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
