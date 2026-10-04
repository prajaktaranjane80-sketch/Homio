import Link from "next/link";
import styles from "./MyHomioFeatureCard.module.css";

export type MyHomioFeatureData = {
  number: string;
  title: string;
  description: string;
  href: string;
};

type Props = {
  item: MyHomioFeatureData;
};

export default function MyHomioFeatureCard({ item }: Props) {
  return (
    <Link href={item.href} className={styles.card}>
      <div className={styles.top}>
        <span className={styles.number}>{item.number}</span>

        <span className={styles.arrow} aria-hidden="true">
          ↗
        </span>
      </div>

      <h3>{item.title}</h3>

      <p>{item.description}</p>
    </Link>
  );
}
