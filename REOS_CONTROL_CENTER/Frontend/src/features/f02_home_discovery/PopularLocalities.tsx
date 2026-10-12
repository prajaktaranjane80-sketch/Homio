import Link from "next/link";
import styles from "./PopularLocalities.module.css";

const localities = [
  {
    city: "Dubai",
    name: "Downtown Dubai",
    type: "Luxury homes · Apartments · Investment",
    href: "/search?city=Dubai&locality=Downtown%20Dubai",
  },
  {
    city: "Dubai",
    name: "Business Bay",
    type: "Apartments · Offices · Commercial",
    href: "/search?city=Dubai&locality=Business%20Bay",
  },
  {
    city: "Dubai",
    name: "Dubai Marina",
    type: "Waterfront homes · Apartments",
    href: "/search?city=Dubai&locality=Dubai%20Marina",
  },
  {
    city: "Singapore",
    name: "Marina Bay",
    type: "Luxury · Commercial · Investment",
    href: "/search?city=Singapore&locality=Marina%20Bay",
  },
  {
    city: "Tokyo",
    name: "Minato",
    type: "Prime residential · Offices · Investment",
    href: "/search?city=Tokyo&locality=Minato",
  },
  {
    city: "London",
    name: "Mayfair",
    type: "Prime residential · Luxury",
    href: "/search?city=London&locality=Mayfair",
  },
];

export default function PopularLocalities() {
  return (
    <section className={styles.section} aria-labelledby="locality-heading">
      <div className="homio-container">
        <div className={styles.header}>
          <div>
            <span className={styles.eyebrow}>LOCALITY DISCOVERY</span>
            <h2 id="locality-heading">Go deeper into the market.</h2>
          </div>

          <Link href="/search" className={styles.viewAll}>
            Explore all locations
            <span aria-hidden="true">↗</span>
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

        <p className={styles.disclaimer}>
          Search results depend on the inventory connected to HOMIO. A
          destination card is not a claim that live properties are available
          in that locality.
        </p>
      </div>
    </section>
  );
}
