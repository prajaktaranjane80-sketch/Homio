import Link from "next/link";
import styles from "./PropertyCollections.module.css";

const collections = [
  {
    title: "Luxury Living",
    description:
      "Exceptional residences, prime locations and premium lifestyle properties.",
    count: "Luxury homes",
    href: "/search?collection=luxury",
    image:
      "https://images.unsplash.com/photo-1600607687920-4e2a09cf159d?auto=format&fit=crop&w=1400&q=85",
  },
  {
    title: "Investment Ready",
    description:
      "Properties selected around location, demand and investment context.",
    count: "Investment",
    href: "/search?collection=investment",
    image:
      "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?auto=format&fit=crop&w=1400&q=85",
  },
  {
    title: "City Apartments",
    description:
      "Connected residences for people who want the city close at hand.",
    count: "Apartments",
    href: "/search?collection=apartments",
    image:
      "https://images.unsplash.com/photo-1493809842364-78817add7ffb?auto=format&fit=crop&w=1400&q=85",
  },
  {
    title: "Family Homes",
    description:
      "More space, more comfort and neighbourhoods built around everyday living.",
    count: "Family",
    href: "/search?collection=family",
    image:
      "https://images.unsplash.com/photo-1600566753086-00f18fb6b3ea?auto=format&fit=crop&w=1400&q=85",
  },
  {
    title: "Waterfront",
    description:
      "Homes shaped by views, open space and a different pace of life.",
    count: "Waterfront",
    href: "/search?collection=waterfront",
    image:
      "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?auto=format&fit=crop&w=1400&q=85",
  },
  {
    title: "Commercial",
    description:
      "Office, retail, hospitality and other commercial opportunities.",
    count: "Commercial",
    href: "/search?intent=commercial",
    image:
      "https://images.unsplash.com/photo-1497366811353-6870744d04b2?auto=format&fit=crop&w=1400&q=85",
  },
];

export default function PropertyCollections() {
  return (
    <section className={styles.section}>
      <div className="homio-container">
        <div className={styles.header}>
          <div>
            <span className={styles.eyebrow}>PROPERTY COLLECTIONS</span>

            <h2>Find a category that fits your journey.</h2>

            <p>
              Start with the kind of property you are looking for, then let
              HOMIO take you deeper into locations, projects and individual
              opportunities.
            </p>
          </div>

          <Link href="/search" className={styles.viewAll}>
            Explore all properties
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
                  Explore <span aria-hidden="true">↗</span>
                </span>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </section>
  );
}
