import Link from "next/link";
import styles from "./ResidentialCollections.module.css";

const collections = [
  {
    title: "Luxury Villas",
    description: "Private residences with space, privacy and premium locations.",
    href: "/search?intent=buy&type=villa&collection=luxury",
    image:
      "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=1400&q=85",
  },
  {
    title: "City Apartments",
    description: "Connected homes for modern urban living.",
    href: "/search?intent=buy&type=apartment",
    image:
      "https://images.unsplash.com/photo-1493809842364-78817add7ffb?auto=format&fit=crop&w=1400&q=85",
  },
  {
    title: "Family Residences",
    description: "Larger spaces designed around everyday life.",
    href: "/search?intent=buy&collection=family",
    image:
      "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?auto=format&fit=crop&w=1400&q=85",
  },
  {
    title: "Waterfront Homes",
    description: "Open views, distinctive settings and premium addresses.",
    href: "/search?intent=buy&collection=waterfront",
    image:
      "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?auto=format&fit=crop&w=1400&q=85",
  },
];

export default function ResidentialCollections() {
  return (
    <section className={styles.section}>
      <div className="homio-container">
        <div className={styles.header}>
          <div>
            <span className={styles.eyebrow}>RESIDENTIAL</span>

            <h2>Homes for different ways of living.</h2>

            <p>
              From city apartments to private villas, discover residential
              opportunities around lifestyle, location and property type.
            </p>
          </div>

          <Link
            href="/search?intent=buy"
            className={styles.viewAll}
          >
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
                  Discover homes
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
