import Link from "next/link";

import type { ProjectOpportunity } from "./project.types";

import styles from "./ProjectInventory.module.css";

type ProjectInventoryProps = Readonly<{
  projectId: string;
  opportunities: ProjectOpportunity[];
}>;

export default function ProjectInventory({
  projectId,
  opportunities,
}: ProjectInventoryProps) {
  return (
    <section
      id="inventory"
      className={styles.section}
      aria-labelledby="project-inventory-title"
    >
      <div className={styles.header}>
        <div>
          <span className={styles.eyebrow}>
            AVAILABLE OPPORTUNITIES
          </span>

          <h2 id="project-inventory-title">
            Explore individual opportunities.
          </h2>

          <p>
            Open a property when verified project inventory is available,
            while keeping the project context intact.
          </p>
        </div>

        <span className={styles.projectRef}>
          Project {projectId}
        </span>
      </div>

      <div className={styles.grid}>
        {opportunities.map((item) => (
          <article
            key={item.id}
            className={styles.card}
          >
            <div className={styles.media}>
              <span>HOMIO OPPORTUNITY</span>
              <strong>{item.configuration}</strong>
            </div>

            <div className={styles.body}>
              <span className={styles.status}>
                {item.status}
              </span>

              <h3>{item.title}</h3>

              <p>{item.context}</p>

              <div className={styles.meta}>
                <div>
                  <span>Value</span>
                  <strong>{item.price}</strong>
                </div>

                <div>
                  <span>Area</span>
                  <strong>{item.area}</strong>
                </div>
              </div>

              {item.href ? (
                <Link
                  href={item.href}
                  className={styles.action}
                >
                  Open property →
                </Link>
              ) : (
                <span
                  className={styles.disabledAction}
                  aria-disabled="true"
                >
                  Preview only
                </span>
              )}
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
