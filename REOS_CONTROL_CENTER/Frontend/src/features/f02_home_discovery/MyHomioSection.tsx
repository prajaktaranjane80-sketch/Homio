import MyHomioFeatureCard, {
  type MyHomioFeatureData,
} from "./MyHomioFeatureCard";
import MyHomioSignInCTA from "./MyHomioSignInCTA";
import styles from "./MyHomioSection.module.css";

const journeyItems: MyHomioFeatureData[] = [
  {
    number: "01",
    title: "Saved properties",
    description:
      "Preview how a list of properties could be organised for later review.",
  },
  {
    number: "02",
    title: "Saved searches",
    description:
      "Preview how consumers could return to previous search criteria.",
  },
  {
    number: "03",
    title: "Compare",
    description:
      "Preview the structure of a property comparison journey.",
  },
  {
    number: "04",
    title: "Upcoming visits",
    description:
      "Preview how scheduled property visits could be presented.",
  },
  {
    number: "05",
    title: "Active conversations",
    description:
      "Preview how property enquiry conversations could be organised.",
  },
  {
    number: "06",
    title: "Transaction journey",
    description:
      "Preview how transaction milestones could appear in one place.",
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
                This is a UI preview. Authentication, persistent saved items,
                visits, conversations and transaction data are not connected
                to these cards yet.
              </p>
            </div>

            <span className={styles.open} aria-disabled="true">
              My HOMIO preview
            </span>
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
