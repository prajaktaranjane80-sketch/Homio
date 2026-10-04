import styles from "./WhyHomioPillar.module.css";

export type WhyHomioPillarData = {
  number: string;
  title: string;
  description: string;
};

type Props = {
  pillar: WhyHomioPillarData;
};

export default function WhyHomioPillar({ pillar }: Props) {
  return (
    <article className={styles.card}>
      <span className={styles.number}>{pillar.number}</span>

      <h3>{pillar.title}</h3>

      <p>{pillar.description}</p>
    </article>
  );
}
