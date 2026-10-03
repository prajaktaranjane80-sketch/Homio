import Link from "next/link";
import styles from "./PopularLocalities.module.css";

const localities = [
  {
    city: "Dubai",
    name: "Downtown Dubai",
    type: "Luxury homes · Apartments · Investment",
    href: "/search?location=downtown-dubai",
  },
  {
    city: "Dubai",
    name: "Business Bay",
    type: "Apartments · Offices · Commercial",
    href: "/search?location=business-bay",
  },
  {
    city: "Dubai",
    name: "Dubai Marina",
    type: "Waterfront homes · Apartments",
    href: "/search?location=dubai-marina",
  },
  {
    city: "Singapore",
    name: "Marina Bay",
    type: "Luxury · Commercial · Investment",
    href: "/search?location=marina-bay",
  },
  {
    city: "Tokyo",
    name: "Minato",
    type: "Prime residential · Offices · Investment",
    href: "/search?location=minato",
  },
  {
    city: "London",
    name: "Mayfair",
    type: "Prime residential · Luxury",
    href: "/search?location=mayfair",
  },
];

export default function PopularLocalities() {
  return (
    <section className={styles.section}>
      <div className="homio-container">
        <div className={styles.header}>
          <div>
            <span className={styles.eyebrow}>LOCALITY DISCOVERY</span>

            <h2>Go deeper into the market.</h2>
          </div>

          <Link href="/search" className={styles.viewAll}>
            Explore all locations <span aria-hidden="true">↗</span>
          </Link>
        </div>

        <div className={styles.grid}>
          {localities.map((locality) => (
            <Link
              key={`${locality.city}-${locality.name}`}
              href={locality.href}
              className={styles.card}
            >
              <div className={styles.top}>
                <span className={styles.city}>{locality.city}</span>

                <span className={styles.arrow} aria-hidden="true">
                  ↗
                </span>
              </div>

              <h3>{locality.name}</h3>

              <p>{locality.type}</p>

              <span className={styles.discover}>Discover locality</span>
            </Link>
          ))}
        </div>
      </div>
    </section>
  );
}
