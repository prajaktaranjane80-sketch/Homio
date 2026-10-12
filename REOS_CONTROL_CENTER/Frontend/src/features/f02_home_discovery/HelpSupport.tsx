import HelpTopicCard, {
  type HelpTopicData,
} from "./HelpTopicCard";
import HelpFAQList from "./HelpFAQList";
import styles from "./HelpSupport.module.css";

const helpItems: HelpTopicData[] = [
  {
    title: "How HOMIO works",
    description:
      "A preview of the discovery, enquiry, visit and brokerage journey.",
  },
  {
    title: "Buying & renting",
    description:
      "Topics consumers should consider before a property decision.",
  },
  {
    title: "Using HOMIO AI",
    description:
      "A concept for search assistance and property context.",
  },
  {
    title: "Account & saved items",
    description:
      "A preview of how a consumer's property journey could be organised.",
  },
];

export default function HelpSupport() {
  return (
    <section id="help" className={styles.section}>
      <div className="homio-container">
        <div className={styles.header}>
          <div>
            <span className={styles.eyebrow}>HELP & SUPPORT</span>

            <h2>Need help finding your way?</h2>

            <p>
              The help cards preview the intended support structure. Dedicated
              help articles, account management and contact workflows are not
              active in this preview.
            </p>
          </div>

          <span className={styles.viewAll} aria-disabled="true">
            Help experience preview
          </span>
        </div>

        <div className={styles.layout}>
          <div className={styles.helpGrid}>
            {helpItems.map((item) => (
              <HelpTopicCard key={item.title} item={item} />
            ))}
          </div>

          <HelpFAQList />
        </div>
      </div>
    </section>
  );
}
