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
            PROJECT PREVIEW OPPORTUNITIES
          </span>

          <h2 id="project-inventory-title">
            Explore individual opportunities.
          </h2>

          <p>
            These are experience-preview records, not live inventory.
            Availability, price and verification are not asserted.
            A property opens only when an existing property reference
            is supplied for that opportunity.
          </p>
        </div>

        <span className={styles.projectRef}>
          Project reference: {projectId}
        </span>
      </div>

      {opportunities.length > 0 ? (
        <div className={styles.grid}>
          {opportunities.map((item) => (
            <article key={item.id} className={styles.card}>
              <div className={styles.media}>
                <span>OPPORTUNITY PREVIEW</span>
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
                    <span>Displayed value</span>
                    <strong>{item.price}</strong>
                  </div>

                  <div>
                    <span>Area</span>
                    <strong>{item.area}</strong>
                  </div>
                </div>

                {item.href ? (
                  <Link href={item.href} className={styles.action}>
                    Open property →
                  </Link>
                ) : (
                  <span
                    className={styles.disabledAction}
                    aria-disabled="true"
                  >
                    Preview only · no property link
                  </span>
                )}
              </div>
            </article>
          ))}
        </div>
      ) : (
        <p
          style={{
            marginTop: 20,
            padding: 20,
            border: "1px dashed #d5dbe2",
            borderRadius: 12,
            color: "#667085",
            fontSize: 13,
            lineHeight: 1.6,
          }}
        >
          No project opportunity records are supplied for this preview.
          No placeholder inventory has been generated.
        </p>
      )}
    </section>
  );
}
