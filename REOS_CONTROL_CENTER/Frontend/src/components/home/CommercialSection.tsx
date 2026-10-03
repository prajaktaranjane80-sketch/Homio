import Link from "next/link";
import styles from "./CommercialSection.module.css";

const categories = [
  {
    title: "Office",
    description: "Workspaces for growing teams, headquarters and investors.",
    href: "/search?intent=commercial&type=office",
    image:
      "https://images.unsplash.com/photo-1497366754035-f200968a6e72?auto=format&fit=crop&w=1200&q=85",
  },
  {
    title: "Retail",
    description: "High-visibility spaces for brands, stores and businesses.",
    href: "/search?intent=commercial&type=retail",
    image:
      "https://images.unsplash.com/photo-1556742049-0cfed4f6a45d?auto=format&fit=crop&w=1200&q=85",
  },
  {
    title: "Hospitality",
    description: "Hotels, serviced residences and hospitality opportunities.",
    href: "/search?intent=commercial&type=hospitality",
    image:
      "https://images.unsplash.com/photo-1564501049412-61c2a3083791?auto=format&fit=crop&w=1200&q=85",
  },
  {
    title: "Industrial",
    description: "Warehouses, logistics and operational real estate.",
    href: "/search?intent=commercial&type=industrial",
    image:
      "https://images.unsplash.com/photo-1565610222536-ef125c59da2e?auto=format&fit=crop&w=1200&q=85",
  },
];

export default function CommercialSection() {
  return (
    <section id="commercial" className={styles.section}>
      <div className="homio-container">
        <div className={styles.hero}>
          <div className={styles.heroContent}>
            <span className={styles.eyebrow}>COMMERCIAL REAL ESTATE</span>

            <h2>
              Property for business,
              <br />
              growth and investment.
            </h2>

            <p>
              Explore commercial opportunities across offices, retail,
              hospitality and industrial markets through the HOMIO brokerage
              journey.
            </p>

            <div className={styles.actions}>
              <Link
                href="/search?intent=commercial"
                className={styles.primaryAction}
              >
                Explore commercial
                <span aria-hidden="true">↗</span>
              </Link>

              <Link
                href="/search?intent=commercial&source=featured"
                className={styles.secondaryAction}
              >
                View featured opportunities
              </Link>
            </div>
          </div>
        </div>

        <div className={styles.categories}>
          {categories.map((category) => (
            <Link
              key={category.title}
              href={category.href}
              className={styles.category}
              style={{ backgroundImage: `url("${category.image}")` }}
            >
              <span className={styles.overlay} />

              <div className={styles.categoryContent}>
                <h3>{category.title}</h3>

                <p>{category.description}</p>

                <span className={styles.explore}>
                  Explore <span aria-hidden="true">→</span>
                </span>
              </div>
            </Link>
          ))}
        </div>

        <div className={styles.bottomBar}>
          <div>
            <span className={styles.bottomLabel}>HOMIO COMMERCIAL</span>

            <strong>
              Discover space with location and market context built in.
            </strong>
          </div>

          <Link href="/search?intent=commercial" className={styles.bottomLink}>
            Start discovery
            <span aria-hidden="true">→</span>
          </Link>
        </div>
      </div>
    </section>
  );
}
