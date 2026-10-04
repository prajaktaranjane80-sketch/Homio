import Link from "next/link";
import HelpTopicCard, {
  type HelpTopicData,
} from "./HelpTopicCard";
import HelpFAQList from "./HelpFAQList";
import styles from "./HelpSupport.module.css";

const helpItems: HelpTopicData[] = [
  {
    title: "How HOMIO works",
    description:
      "Understand discovery, enquiry, visits and the brokerage journey.",
    href: "/help/how-homio-works",
  },
  {
    title: "Buying & renting",
    description:
      "Get practical answers before making a property decision.",
    href: "/help/buying-renting",
  },
  {
    title: "Using HOMIO AI",
    description:
      "Learn how AI can refine searches and explain property context.",
    href: "/help/homio-ai",
  },
  {
    title: "Account & saved items",
    description:
      "Manage saved properties, searches and your HOMIO journey.",
    href: "/help/account",
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
              Get practical guidance about using HOMIO, managing your journey
              and taking the next step.
            </p>
          </div>

          <Link href="/help" className={styles.viewAll}>
            Visit Help Center
            <span aria-hidden="true">↗</span>
          </Link>
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
