import Link from "next/link";

import styles from "./HomeQuickDiscovery.module.css";

const discoveries = [
  {
    title: "Buy a Home",
    description:
      "Explore the home-buying search experience across Pune neighbourhoods.",
    href: "/search?intent=buy&country=India&city=Pune",
  },
  {
    title: "Rent a Home",
    description:
      "Start a Pune rental search and refine your property preferences.",
    href: "/search?intent=rent&country=India&city=Pune",
  },
  {
    title: "New Projects",
    description:
      "Explore the project-discovery experience for Pune.",
    href: "/search?intent=projects&country=India&city=Pune",
  },
  {
    title: "Commercial Spaces",
    description:
      "Open Pune-focused discovery for offices and commercial property.",
    href: "/search?intent=commercial&country=India&city=Pune",
  },
];

export default function HomeQuickDiscovery() {
  return (
    <section id="explore" className={styles.section}>
      <div className="homio-container">
        <div className={styles.heading}>
          <div>
            <span className={styles.eyebrow}>
              EXPLORE PUNE WITH HOMIO
            </span>

            <h2>Start with what you are looking for.</h2>
          </div>

          <p>
            Choose a property journey, then narrow your search by
            locality and preferences. Search previews and property
            facts remain subject to their actual source status.
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
