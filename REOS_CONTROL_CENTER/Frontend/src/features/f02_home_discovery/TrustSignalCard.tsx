import styles from "./TrustSignalCard.module.css";

export type TrustSignalCardData = {
  number: string;
  title: string;
  description: string;
};

type Props = {
  signal: TrustSignalCardData;
};

export default function TrustSignalCard({ signal }: Props) {
  return (
    <article className={styles.card}>
      <div className={styles.top}>
        <span className={styles.number}>{signal.number}</span>

        <span className={styles.check} aria-hidden="true">
          ✓
        </span>
      </div>

      <h3>{signal.title}</h3>

      <p>{signal.description}</p>
    </article>
  );
}
