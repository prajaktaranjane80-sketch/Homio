import Link from "next/link";
import styles from "./SavedPreviewCard.module.css";

export type SavedPreviewCardData = {
  type: string;
  title: string;
  location: string;
  price: string;
  image: string;
};

type Props = {
  item: SavedPreviewCardData;
};

export default function SavedPreviewCard({ item }: Props) {
  return (
    <article className={styles.item}>
      <div className={styles.imageWrap}>
        <img src={item.image} alt="" className={styles.image} loading="lazy" />
      </div>

      <div className={styles.body}>
        <span>{item.type}</span>

        <Link href="/saved">{item.title}</Link>

        <p>{item.location}</p>

        <strong>{item.price}</strong>
      </div>

      <Link
        href="/saved"
        className={styles.arrow}
        aria-label={`Open ${item.title}`}
      >
        ↗
      </Link>
    </article>
  );
}
