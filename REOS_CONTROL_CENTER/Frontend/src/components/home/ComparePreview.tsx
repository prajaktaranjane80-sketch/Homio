import Link from "next/link";
import styles from "./ComparePreview.module.css";

type Props = {
  items: {
    title: string;
    image: string;
  }[];
};

const attributes = [
  "Price and size",
  "Property type",
  "Location context",
  "Project information",
  "Availability signals",
];

export default function ComparePreview({ items }: Props) {
  return (
    <div className={styles.panel}>
      <div className={styles.visual}>
        <div className={styles.header}>
          <span>COMPARE</span>
          <small>{items.length} selected</small>
        </div>

        <div className={styles.cards}>
          {items.map((item, index) => (
            <div key={item.title} className={styles.card}>
              <img src={item.image} alt="" />
              <span>{index + 1}</span>
            </div>
          ))}
        </div>

        <div className={styles.rows}>
          {attributes.map((attribute) => (
            <div key={attribute}>
              <span>{attribute}</span>
              <strong>Compare</strong>
            </div>
          ))}
        </div>
      </div>

      <div className={styles.body}>
        <h3>Compare before you decide.</h3>

        <p>
          See the differences across the properties you are actually
          considering.
        </p>

        <Link href="/compare">
          Start comparing
          <span aria-hidden="true">→</span>
        </Link>
      </div>
    </div>
  );
}
