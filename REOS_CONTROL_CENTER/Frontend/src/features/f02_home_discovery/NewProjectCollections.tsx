import Link from "next/link";
import styles from "./NewProjectCollections.module.css";

const collections = [
  {
    title: "New Launches",
    subtitle: "Explore a new-development experience preview",
    label: "Project preview",
    href: "/project/harbour-residences",
    image:
      "https://images.unsplash.com/photo-1600607687920-4e2a09cf159d?auto=format&fit=crop&w=1400&q=85",
  },
  {
    title: "Waterfront Living",
    subtitle: "Explore a waterfront-style project preview",
    label: "Project preview",
    href: "/project/marina-crest",
    image:
      "https://images.unsplash.com/photo-1494526585095-c41746248156?auto=format&fit=crop&w=1400&q=85",
  },
  {
    title: "Smart Investments",
    subtitle: "Explore a project-detail preview",
    label: "Project preview",
    href: "/project/the-meridian",
    image:
      "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?auto=format&fit=crop&w=1400&q=85",
  },
  {
    title: "Family Residences",
    subtitle: "Explore a residential project collection preview",
    label: "Collection preview",
    href: "/project/pune-east-collection-001",
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
            These cards open project-experience previews. Pricing, live
            inventory, project counts and availability are not authoritative
            REOS data.
          </p>
        </div>

        <div className={styles.grid}>
          {collections.map((collection) => (
            <Link
              key={collection.title}
              href={collection.href}
              className={styles.card}
              style={{
                backgroundImage: `url("${collection.image}")`,
              }}
            >
              <span className={styles.overlay} />

              <div className={styles.content}>
                <span className={styles.count}>{collection.label}</span>
                <h3>{collection.title}</h3>
                <p>{collection.subtitle}</p>

                <span className={styles.link}>
                  Open project preview
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
