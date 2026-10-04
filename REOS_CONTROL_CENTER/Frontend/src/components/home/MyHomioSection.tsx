import Link from "next/link";
import styles from "./MyHomioSection.module.css";

const journeyItems = [
  {
    title: "Saved properties",
    description: "Keep the homes and projects you want to revisit.",
    href: "/saved",
  },
  {
    title: "Saved searches",
    description: "Return to searches without rebuilding your criteria.",
    href: "/my",
  },
  {
    title: "Compare",
    description: "Continue evaluating the properties on your shortlist.",
    href: "/compare",
  },
  {
    title: "Upcoming visits",
    description: "Stay on top of scheduled property visits and actions.",
    href: "/my",
  },
  {
    title: "Active conversations",
    description: "Continue relevant HOMIO enquiries and communication.",
    href: "/my",
  },
  {
    title: "Transaction journey",
    description: "Follow important deal milestones when you move forward.",
    href: "/my",
  },
];

export default function MyHomioSection() {
  return (
    <section id="my-homio" className={styles.section}>
      <div className="homio-container">
        <div className={styles.shell}>
          <div className={styles.header}>
            <div>
              <span className={styles.eyebrow}>MY HOMIO</span>

              <h2>Your property journey, in one place.</h2>

              <p>
                Keep your saved properties, searches, comparisons, visits,
                conversations and transaction actions connected.
              </p>
            </div>

            <Link href="/my" className={styles.open}>
              Open My HOMIO
              <span aria-hidden="true">↗</span>
            </Link>
          </div>

          <div className={styles.grid}>
            {journeyItems.map((item, index) => (
              <Link key={item.title} href={item.href} className={styles.card}>
                <div className={styles.cardTop}>
                  <span className={styles.number}>
                    {String(index + 1).padStart(2, "0")}
                  </span>

                  <span className={styles.arrow} aria-hidden="true">
                    ↗
                  </span>
                </div>

                <h3>{item.title}</h3>

                <p>{item.description}</p>
              </Link>
            ))}
          </div>

          <div className={styles.signIn}>
            <div>
              <strong>Pick up where you left off.</strong>
              <p>
                Sign in to keep your discovery and brokerage journey connected
                across devices.
              </p>
            </div>

            <Link href="/my">Continue to My HOMIO</Link>
          </div>
        </div>
      </div>
    </section>
  );
}
