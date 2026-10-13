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
    <section
      className={styles.section}
      aria-labelledby="related-projects-title"
    >
      <div className={styles.header}>
        <div>
          <span className={styles.eyebrow}>
            RELATED DISCOVERY
          </span>

          <h2 id="related-projects-title">
            Keep exploring beyond one project.
          </h2>
        </div>

        <span className={styles.context}>
          Around {project.city}
        </span>
      </div>

      {project.relatedProjects.length > 0 ? (
        <div className={styles.grid}>
          {project.relatedProjects.map((item, index) => (
            <article key={item.id} className={styles.card}>
              <div
                className={`${styles.visual} ${
                  index % 2 === 0
                    ? styles.visualLight
                    : styles.visualCool
                }`}
                aria-hidden="true"
              >
                <span className={styles.visualLabel}>
                  PROJECT PREVIEW
                </span>

                <span className={styles.visualMonogram}>
                  H
                </span>
              </div>

              <div className={styles.body}>
                <span className={styles.location}>
                  {item.location}
                </span>

                <h3>{item.name}</h3>

                <p>{item.highlight}</p>

                <Link
                  href={`/project/${item.id}`}
                  className={styles.action}
                  aria-label={`Explore project ${item.name}`}
                >
                  Explore project
                  <span aria-hidden="true">→</span>
                </Link>
              </div>
            </article>
          ))}
        </div>
      ) : (
        <p className={styles.emptyState}>
          Related project discovery is not connected for this preview.
          Confirmed projects will appear when an approved source is available.
        </p>
      )}

      <p className={styles.note}>
        Related project references are experience-preview links until
        verified project discovery capability is connected.
      </p>
    </section>
  );
}
