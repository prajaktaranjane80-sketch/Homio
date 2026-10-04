import Link from "next/link";
import styles from "./HelpTopicCard.module.css";

export type HelpTopicData = {
  title: string;
  description: string;
  href: string;
};

type Props = {
  item: HelpTopicData;
};

export default function HelpTopicCard({ item }: Props) {
  return (
    <Link href={item.href} className={styles.card}>
      <span className={styles.icon} aria-hidden="true">
        ?
      </span>

      <h3>{item.title}</h3>

      <p>{item.description}</p>

      <span className={styles.link}>
        Learn more
        <span aria-hidden="true">→</span>
      </span>
    </Link>
  );
}
