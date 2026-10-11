import Link from "next/link";

import styles from "./HomeQuickDiscovery.module.css";

const discoveries = [
  {
    title: "Premium Homes",
    description: "Explore premium residences in the current preview inventory.",
    href: "/search?q=premium",
  },
  {
    title: "New Projects",
    description: "Explore project-oriented property discovery.",
    href: "/search?intent=projects",
  },
  {
    title: "Commercial",
    description: "Open the commercial property search context.",
    href: "/search?intent=commercial",
  },
  {
    title: "Ready to Move",
    description: "Explore preview properties marked ready to move.",
    href: "/search?status=Ready%20to%20move",
  },
];

export default function HomeQuickDiscovery() {
  return (
    <section id="explore" className={styles.section}>
      <div className="homio-container">
        <div className={styles.heading}>
          <div>
            <span className={styles.eyebrow}>DISCOVER HOMIO</span>
            <h2>Start with what matters to you.</h2>
          </div>

          <p>
            Move from broad discovery to a focused HOMIO brokerage journey
            without navigating a broker marketplace.
          </p>
        </div>

        <div className={styles.grid}>
          {discoveries.map((item) => (
            <Link
              key={item.title}
              href={item.href}
              className={styles.card}
            >
              <span className={styles.arrow} aria-hidden="true">
                ↗
              </span>

              <h3>{item.title}</h3>
              <p>{item.description}</p>
            </Link>
          ))}
        </div>
      </div>
    </section>
  );
}
