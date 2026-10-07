import Link from "next/link";
import styles from "./PropertyUnavailable.module.css";

type PropertyUnavailableProps = Readonly<{
  title?: string;
  description?: string;
}>;

export default function PropertyUnavailable({
  title = "Property information is temporarily unavailable.",
  description =
    "HOMIO could not load the authoritative property information required for this view.",
}: PropertyUnavailableProps) {
  return (
    <main className={styles.page}>
      <div className="homio-container">
        <section className={styles.card}>
          <span className={styles.eyebrow}>HOMIO PROPERTY</span>
          <h1>{title}</h1>
          <p>{description}</p>

          <div className={styles.actions}>
            <Link href="/search" className={styles.primary}>
              Return to search
            </Link>

            <Link href="/" className={styles.secondary}>
              Go to HOMIO
            </Link>
          </div>
        </section>
      </div>
    </main>
  );
}
