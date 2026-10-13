import Link from "next/link";
import styles from "./VerifiedProperties.module.css";

const properties = [
  {
    id: "palm-view-residence",
    title: "Palm View Residence",
    location: "Palm Jumeirah, Dubai",
    type: "4 Bed Villa",
    price: "AED 8.90M",
    image:
      "https://images.unsplash.com/photo-1600047509358-9dc75507daeb?auto=format&fit=crop&w=1400&q=85",
    signals: [
      "Illustrative property details",
      "Location not independently verified",
      "Availability not confirmed",
    ],
  },
  {
    id: "central-garden-residence",
    title: "Central Garden Residence",
    location: "Bukit Timah, Singapore",
    type: "3 Bed Residence",
    price: "SGD 3.40M",
    image:
      "https://images.unsplash.com/photo-1600566753190-17f0baa2a6c3?auto=format&fit=crop&w=1400&q=85",
    signals: [
      "Illustrative property details",
      "Location not independently verified",
      "Availability not confirmed",
    ],
  },
  {
    id: "prime-metropolitan-home",
    title: "Prime Metropolitan Home",
    location: "Shibuya, Tokyo",
    type: "2 Bed Apartment",
    price: "JPY 145M",
    image:
      "https://images.unsplash.com/photo-1600607687920-4e2a09cf159d?auto=format&fit=crop&w=1400&q=85",
    signals: [
      "Illustrative property details",
      "Location not independently verified",
      "Availability not confirmed",
    ],
  },
];

export default function VerifiedProperties() {
  return (
    <section
      className={styles.section}
      aria-labelledby="property-preview-title"
    >
      <div className="homio-container">
        <div className={styles.top}>
          <div className={styles.heading}>
            <span className={styles.eyebrow}>
              PROPERTY EXPERIENCE PREVIEWS
            </span>

            <h2 id="property-preview-title">
              See how property details will be presented.
            </h2>

            <p>
              These sample listings demonstrate the HOMIO discovery
              experience. Property information, prices, locations and
              availability shown here are illustrative, not verified live
              inventory.
            </p>
          </div>

          <aside
            className={styles.trustBox}
            aria-label="Property preview disclaimer"
          >
            <span className={styles.trustIcon} aria-hidden="true">
              i
            </span>

            <div>
              <strong>A clear preview, not a verification.</strong>

              <p>
                Verification status must come from an authoritative
                source. A sample image or property description is not
                proof of ownership, accuracy or availability.
              </p>
            </div>
          </aside>
        </div>

        <div className={styles.grid}>
          {properties.map((property) => (
            <article key={property.id} className={styles.card}>
              <Link
                href={`/property/${property.id}`}
                className={styles.imageLink}
                aria-label={`View preview of ${property.title}`}
              >
                <div className={styles.imageWrap}>
                  
                  <Image
                    src={property.image}
                    width={1400}
                    height={1050}
                    sizes="(max-width: 640px) 100vw, (max-width: 900px) 50vw, 33vw"
                    alt={`Illustrative property image for ${property.title}`}
                    className={styles.image}
                    loading="lazy"
                  />


                  <span className={styles.previewBadge}>
                    <span
                      className={styles.previewDot}
                      aria-hidden="true"
                    />
                    Experience preview · not verified
                  </span>
                </div>
              </Link>

              <div className={styles.body}>
                <div className={styles.type}>{property.type}</div>

                <Link
                  href={`/property/${property.id}`}
                  className={styles.title}
                >
                  {property.title}
                </Link>

                <p className={styles.location}>{property.location}</p>

                <div
                  className={styles.signals}
                  aria-label="Preview information status"
                >
                  {property.signals.map((signal) => (
                    <div key={signal} className={styles.signal}>
                      <span
                        className={styles.signalMark}
                        aria-hidden="true"
                      >
                        i
                      </span>
                      <span>{signal}</span>
                    </div>
                  ))}
                </div>

                <div className={styles.footer}>
                  <div className={styles.priceGroup}>
                    <span className={styles.priceLabel}>
                      Illustrative price
                    </span>
                    <strong className={styles.price}>
                      {property.price}
                    </strong>
                  </div>

                  <Link
                    href={`/property/${property.id}`}
                    className={styles.action}
                  >
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
