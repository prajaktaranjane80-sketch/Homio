import Link from "next/link";

import type { ProjectRecord } from "./project.types";

import styles from "./RelatedProjects.module.css";

type RelatedProjectsProps = Readonly<{
  project: ProjectRecord;
}>;

export default function RelatedProjects({
  project,
}: RelatedProjectsProps) {
  return (
    <section className={styles.section}>
      <div className={styles.header}>
        <div>
          <span className={styles.eyebrow}>
            RELATED DISCOVERY
          </span>

          <h2>
            Keep exploring beyond one project.
          </h2>
        </div>

        <span className={styles.context}>
          Around {project.city}
        </span>
      </div>

      <div className={styles.grid}>
        {project.relatedProjects.map((item) => (
          <article
            key={item.id}
            className={styles.card}
          >
            <div className={styles.visual}>
              <span>HOMIO PROJECT</span>
            </div>

            <div className={styles.body}>
              <span>{item.location}</span>

              <h3>{item.name}</h3>

              <p>{item.highlight}</p>

              <Link
                href={`/project/${item.id}`}
                className={styles.action}
              >
                Explore project →
              </Link>
            </div>
          </article>
        ))}
      </div>

      <p className={styles.note}>
        Related project references are experience-preview links until
        verified project discovery capability is connected.
      </p>
    </section>
  );
}
