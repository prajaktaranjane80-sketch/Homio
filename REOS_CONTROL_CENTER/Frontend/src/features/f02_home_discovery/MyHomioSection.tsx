import Link from "next/link";
import MyHomioFeatureCard, {
  type MyHomioFeatureData,
} from "./MyHomioFeatureCard";
import MyHomioSignInCTA from "./MyHomioSignInCTA";
import styles from "./MyHomioSection.module.css";

const journeyItems: MyHomioFeatureData[] = [
  {
    number: "01",
    title: "Saved properties",
    description: "Keep the homes and projects you want to revisit.",
    href: "/saved",
  },
  {
    number: "02",
    title: "Saved searches",
    description: "Return to searches without rebuilding your criteria.",
    href: "/my",
  },
  {
    number: "03",
    title: "Compare",
    description: "Continue evaluating the properties on your shortlist.",
    href: "/compare",
  },
  {
    number: "04",
    title: "Upcoming visits",
    description: "Stay on top of scheduled property visits and actions.",
    href: "/my",
  },
  {
    number: "05",
    title: "Active conversations",
    description: "Continue relevant HOMIO enquiries and communication.",
    href: "/my",
  },
  {
    number: "06",
    title: "Transaction journey",
    description:
      "Follow important deal milestones when you move forward.",
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
            {journeyItems.map((item) => (
              <MyHomioFeatureCard key={item.number} item={item} />
            ))}
          </div>

          <MyHomioSignInCTA />
        </div>
      </div>
    </section>
  );
}
