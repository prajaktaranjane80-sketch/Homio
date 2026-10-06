import type { PropertyRecord } from "./property.types";
import styles from "./SimilarProperties.module.css";

type SimilarPropertiesProps = Readonly<{
  property: PropertyRecord;
}>;

const similar = [
  {
    title: "Premium 3 BHK Residence",
    location: "Viman Nagar, Pune",
    price: "₹1.95 Cr",
    area: "1,640 sq.ft.",
  },
  {
    title: "Elegant 4 BHK Residence",
    location: "Aundh, Pune",
    price: "₹2.85 Cr",
    area: "2,250 sq.ft.",
  },
  {
    title: "Modern 2 BHK City Home",
    location: "Baner, Pune",
    price: "₹1.28 Cr",
    area: "1,220 sq.ft.",
  },
];

export default function SimilarProperties({
  property,
}: SimilarPropertiesProps) {
  return (
    <section className={styles.section}>
      <div className={styles.header}>
        <div>
          <span className={styles.eyebrow}>SIMILAR DISCOVERY</span>
          <h2>More properties worth exploring.</h2>
        </div>

        <span className={styles.context}>
          Around {property.locality}
        </span>
      </div>

      <div className={styles.grid}>
        {similar.map((item) => (
          <article key={item.title} className={styles.card}>
            <div className={styles.media}>
              <span>HOMIO PROPERTY</span>
            </div>

            <div className={styles.body}>
              <span className={styles.type}>Residential</span>
              <h3>{item.title}</h3>
              <p>{item.location}</p>

              <div className={styles.meta}>
                <strong>{item.price}</strong>
                <span>{item.area}</span>
              </div>

              <button type="button">View property →</button>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
