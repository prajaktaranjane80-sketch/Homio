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
      "Your selected homes and spaces, once the account persistence service is connected.",
  },
  {
    number: "02",
    title: "Saved searches",
    description:
      "Return to previous search criteria after search synchronisation is enabled.",
  },
  {
    number: "03",
    title: "Compare",
    description:
      "Review shortlisted properties when the comparison service is connected.",
  },
  {
    number: "04",
    title: "Upcoming visits",
    description:
      "See confirmed visit details after the visits service becomes available.",
  },
  {
    number: "05",
    title: "Active conversations",
    description:
      "Keep enquiry conversations together when the messaging service is connected.",
  },
  {
    number: "06",
    title: "Transaction journey",
    description:
      "Follow authorized transaction milestones when the transaction service is connected.",
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
                Sign in to your HOMIO account. The cards below describe planned account features;
                saved items, visits, conversations and transaction records are not yet backed by
                connected persistence services.
              </p>
            </div>
            <span className={styles.open} aria-disabled="true">
              Account features
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