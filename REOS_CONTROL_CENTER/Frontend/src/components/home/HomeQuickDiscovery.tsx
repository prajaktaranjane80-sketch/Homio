import Link from "next/link";
import styles from "./HomeQuickDiscovery.module.css";

const discoveries = [
  {
    title: "Luxury Homes",
    description: "Discover premium residences in global destinations.",
    href: "/search?collection=luxury",
  },
  {
    title: "New Projects",
    description: "Explore upcoming and newly launched developments.",
    href: "/search?intent=projects",
  },
  {
    title: "Commercial",
    description: "Office, retail, hospitality and investment opportunities.",
    href: "/search?intent=commercial",
  },
  {
    title: "Verified",
    description: "Browse inventory with stronger trust signals.",
    href: "/search?filter=verified",
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
            <Link key={item.title} href={item.href} className={styles.card}>
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
