import styles from "./HelpTopicCard.module.css";

export type HelpTopicData = {
  title: string;
  description: string;
};

type Props = {
  item: HelpTopicData;
};

export default function HelpTopicCard({ item }: Props) {
  return (
    <article className={styles.card} aria-disabled="true">
      <span className={styles.icon} aria-hidden="true">
        ?
      </span>

      <h3>{item.title}</h3>

      <p>{item.description}</p>

      <span className={styles.link}>
        Help article preview · not active
      </span>
    </article>
  );
}
