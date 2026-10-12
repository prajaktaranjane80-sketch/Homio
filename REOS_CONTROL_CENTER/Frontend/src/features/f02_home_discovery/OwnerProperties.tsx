import Link from "next/link";
import styles from "./OwnerProperties.module.css";

const properties = [
  {
    title: "Modern City Residence",
    location: "Jumeirah Village Circle, Dubai",
    type: "2 Bed Apartment",
    price: "AED 1.35M",
    area: "1,180 sq.ft",
    image:
      "https://images.unsplash.com/photo-1600585154526-990dced4db0d?auto=format&fit=crop&w=1400&q=85",
    href: "/property/modern-city-residence",
  },
  {
    title: "Parkside Family Home",
    location: "Singapore",
    type: "3 Bed Residence",
    price: "SGD 2.20M",
    area: "1,540 sq.ft",
    image:
      "https://images.unsplash.com/photo-1600047509807-ba8f99d2cdde?auto=format&fit=crop&w=1400&q=85",
    href: "/property/parkside-family-home",
  },
  {
    title: "Prime Urban Apartment",
    location: "Minato, Tokyo",
    type: "2 Bed Apartment",
    price: "JPY 128M",
    area: "890 sq.ft",
    image:
      "https://images.unsplash.com/photo-1600607687920-4e2a09cf159d?auto=format&fit=crop&w=1400&q=85",
    href: "/property/prime-urban-apartment",
  },
];

export default function OwnerProperties() {
  return (
    <section className={styles.section} aria-labelledby="owner-preview-heading">
      <div className="homio-container">
        <div className={styles.header}>
          <div>
            <span className={styles.eyebrow}>
              OWNER-ORIGIN EXPERIENCE PREVIEWS
            </span>

            <h2 id="owner-preview-heading">
              See how owner-origin listings could appear.
            </h2>

            <p>
              These are illustrative property cards, not verified owner
              listings. Ownership, listing authority, prices, property facts
              and availability have not been independently confirmed.
            </p>
          </div>

          <Link href="/search?intent=buy" className={styles.viewAll}>
            Browse property previews
            <span aria-hidden="true">↗</span>
          </Link>
        </div>

        <div className={styles.layout}>
          <article className={styles.featured}>
            <div className={styles.featuredImageWrap}>
              <img
                src={properties[0].image}
                alt={`Illustrative image for ${properties[0].title}`}
                className={styles.featuredImage}
                loading="lazy"
              />

              <span className={styles.ownerBadge}>
                Owner-origin preview · not verified
              </span>
            </div>

            <div className={styles.featuredBody}>
              <div>
                <span className={styles.type}>{properties[0].type}</span>

                <Link
                  href={properties[0].href}
                  className={styles.featuredTitle}
                >
                  {properties[0].title}
                </Link>

                <p>{properties[0].location}</p>
              </div>

              <div className={styles.featuredMeta}>
                <strong>{properties[0].price}</strong>
                <span>{properties[0].area}</span>
              </div>
            </div>
          </article>

          <div className={styles.sideList}>
            {properties.slice(1).map((property) => (
              <article key={property.title} className={styles.sideCard}>
                <Link href={property.href} className={styles.sideImageLink}>
                  <div className={styles.sideImageWrap}>
                    <img
                      src={property.image}
                      alt={`Illustrative image for ${property.title}`}
                      className={styles.sideImage}
                      loading="lazy"
                    />

                    <span className={styles.ownerBadgeSmall}>
                      Preview · not verified
                    </span>
                  </div>
                </Link>

                <div className={styles.sideBody}>
                  <span className={styles.type}>{property.type}</span>

                  <Link href={property.href} className={styles.sideTitle}>
                    {property.title}
                  </Link>

                  <p>{property.location}</p>

                  <div className={styles.sideMeta}>
                    <strong>{property.price}</strong>
                    <span>{property.area}</span>
                  </div>
                </div>
              </article>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
