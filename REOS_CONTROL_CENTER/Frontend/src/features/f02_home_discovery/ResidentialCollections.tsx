import Link from "next/link";
import styles from "./ResidentialCollections.module.css";

const collections = [
  {
    title: "Luxury Villas",
    description:
      "Explore villa-type property examples. Luxury inventory is not independently verified.",
    href: "/search?intent=buy&propertyType=Villa&q=luxury",
    image:
      "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=1400&q=85",
  },
  {
    title: "City Apartments",
    description:
      "Search apartment-type properties using the supported HOMIO search criteria.",
    href: "/search?intent=buy&propertyType=Apartment",
    image:
      "https://images.unsplash.com/photo-1493809842364-78817add7ffb?auto=format&fit=crop&w=1400&q=85",
  },
  {
    title: "Family Residences",
    description:
      "Explore the family-home search concept against the available preview dataset.",
    href: "/search?intent=buy&q=family",
    image:
      "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?auto=format&fit=crop&w=1400&q=85",
  },
  {
    title: "Waterfront Homes",
    description:
      "Open a waterfront-related search. Results depend on the connected property data.",
    href: "/search?intent=buy&q=waterfront",
    image:
      "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?auto=format&fit=crop&w=1400&q=85",
  },
];

export default function ResidentialCollections() {
  return (
    <section
      className={styles.section}
      aria-labelledby="residential-collections-heading"
    >
      <div className="homio-container">
        <div className={styles.header}>
          <div>
            <span className={styles.eyebrow}>RESIDENTIAL</span>

            <h2 id="residential-collections-heading">
              Homes for different ways of living.
            </h2>

            <p>
              Start with property type or a search term, then explore the
              available results. These collection cards are discovery
              pathways, not claims of verified or live inventory.
            </p>
          </div>

          <Link href="/search?intent=buy" className={styles.viewAll}>
            Explore homes
            <span aria-hidden="true">↗</span>
          </Link>
        </div>

        <div className={styles.grid}>
          {collections.map((collection, index) => (
            <Link
              key={collection.title}
              href={collection.href}
              className={`${styles.card} ${
                index === 0 ? styles.featured : ""
              }`}
              style={{ backgroundImage: `url("${collection.image}")` }}
            >
              <span className={styles.overlay} />

              <div className={styles.content}>
                <span className={styles.number}>
                  {String(index + 1).padStart(2, "0")}
                </span>

                <h3>{collection.title}</h3>
                <p>{collection.description}</p>

                <span className={styles.explore}>
                  Open property search
                  <span aria-hidden="true">→</span>
                </span>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </section>
  );
}
