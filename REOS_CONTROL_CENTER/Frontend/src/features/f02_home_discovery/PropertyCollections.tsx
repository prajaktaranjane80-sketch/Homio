import Link from "next/link";
import styles from "./PropertyCollections.module.css";

const collections = [
  {
    title: "Luxury Living",
    description:
      "Explore premium-style residences through the available property preview.",
    count: "Property preview",
    href: "/search?intent=buy&propertyType=Villa",
    image:
      "https://images.unsplash.com/photo-1600607687920-4e2a09cf159d?auto=format&fit=crop&w=1400&q=85",
  },
  {
    title: "Investment Ready",
    description:
      "Search preview records with investment-related property context.",
    count: "Search preview",
    href: "/search?intent=buy&q=investment",
    image:
      "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?auto=format&fit=crop&w=1400&q=85",
  },
  {
    title: "City Apartments",
    description:
      "Explore apartments available in the currently connected search preview.",
    count: "Apartments",
    href: "/search?intent=buy&propertyType=Apartment",
    image:
      "https://images.unsplash.com/photo-1493809842364-78817add7ffb?auto=format&fit=crop&w=1400&q=85",
  },
  {
    title: "Family Homes",
    description:
      "Search for property examples with family-oriented context.",
    count: "Search preview",
    href: "/search?intent=buy&q=family",
    image:
      "https://images.unsplash.com/photo-1600566753086-00f18fb6b3ea?auto=format&fit=crop&w=1400&q=85",
  },
  {
    title: "Waterfront",
    description:
      "Explore the waterfront search term against the available preview data.",
    count: "Search preview",
    href: "/search?intent=buy&q=waterfront",
    image:
      "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?auto=format&fit=crop&w=1400&q=85",
  },
  {
    title: "Commercial",
    description:
      "Open commercial search. Commercial inventory is not yet connected.",
    count: "Commercial preview",
    href: "/search?intent=commercial",
    image:
      "https://images.unsplash.com/photo-1497366811353-6870744d04b2?auto=format&fit=crop&w=1400&q=85",
  },
];

export default function PropertyCollections() {
  return (
    <section className={styles.section} aria-labelledby="property-collections-heading">
      <div className="homio-container">
        <div className={styles.header}>
          <div>
            <span className={styles.eyebrow}>PROPERTY COLLECTIONS</span>
            <h2 id="property-collections-heading">
              Find a category that fits your journey.
            </h2>

            <p>
              Collection cards open supported search criteria. They do not
              represent a verified or curated live inventory feed.
            </p>
          </div>

          <Link href="/search?intent=buy" className={styles.viewAll}>
            Explore property search
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
                <span className={styles.count}>{collection.count}</span>
                <h3>{collection.title}</h3>
                <p>{collection.description}</p>

                <span className={styles.explore}>
                  Open search
                  <span aria-hidden="true">↗</span>
                </span>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </section>
  );
}
