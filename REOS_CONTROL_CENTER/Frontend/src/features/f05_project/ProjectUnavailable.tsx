import Link from "next/link";

import styles from "./ProjectUnavailable.module.css";

type ProjectUnavailableProps = Readonly<{
  title: string;
  description: string;
}>;

export default function ProjectUnavailable({
  title,
  description,
}: ProjectUnavailableProps) {
  return (
    <main className={styles.page}>
      <div className="homio-container">
        <section className={styles.card}>
          <span className={styles.eyebrow}>
            HOMIO PROJECT
          </span>

          <h1>{title}</h1>

          <p>{description}</p>

          <div className={styles.actions}>
            <Link
              href="/search?intent=projects"
              className={styles.primary}
            >
              Explore projects
            </Link>

            <Link
              href="/"
              className={styles.secondary}
            >
              Return home
            </Link>
          </div>
        </section>
      </div>
    </main>
  );
}
