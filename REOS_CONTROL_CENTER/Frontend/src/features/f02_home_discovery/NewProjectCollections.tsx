import Link from "next/link";
import styles from "./NewProjectCollections.module.css";

const collections = [
  {
    title: "New Launches",
    subtitle: "Be early to the market",
    count: "24 projects",
    href: "/search?collection=new-launches",
    image:
      "https://images.unsplash.com/photo-1600607687920-4e2a09cf159d?auto=format&fit=crop&w=1400&q=85",
  },
  {
    title: "Waterfront Living",
    subtitle: "Homes with a different horizon",
    count: "18 projects",
    href: "/search?collection=waterfront",
    image:
      "https://images.unsplash.com/photo-1494526585095-c41746248156?auto=format&fit=crop&w=1400&q=85",
  },
  {
    title: "Smart Investments",
    subtitle: "Growth-oriented opportunities",
    count: "31 projects",
    href: "/search?collection=investment",
    image:
      "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?auto=format&fit=crop&w=1400&q=85",
  },
  {
    title: "Family Residences",
    subtitle: "Designed around everyday life",
    count: "42 projects",
    href: "/search?collection=family",
    image:
      "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=1400&q=85",
  },
];

export default function NewProjectCollections() {
  return (
    <section className={styles.section}>
      <div className="homio-container">
        <div className={styles.heading}>
          <div>
            <span className={styles.eyebrow}>PROJECT COLLECTIONS</span>

            <h2>Explore by the way you want to live.</h2>
          </div>

          <p>
            Curated discovery paths help you move from thousands of
            possibilities to a focused set of developments.
          </p>
        </div>

        <div className={styles.grid}>
          {collections.map((collection) => (
            <Link
              key={collection.title}
              href={collection.href}
              className={styles.card}
              style={{ backgroundImage: `url("${collection.image}")` }}
            >
              <span className={styles.overlay} />

              <div className={styles.content}>
                <span className={styles.count}>{collection.count}</span>

                <h3>{collection.title}</h3>

                <p>{collection.subtitle}</p>

                <span className={styles.link}>
                  Explore collection <span aria-hidden="true">↗</span>
                </span>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </section>
  );
}
