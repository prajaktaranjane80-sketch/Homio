import Link from "next/link";

import type { ProjectOpportunity } from "./project.types";
import styles from "./ProjectInventory.module.css";

type ProjectInventoryProps = Readonly<{
  projectId: string;
  opportunities: ProjectOpportunity[];
}>;

function isPreviewOpportunity(item: ProjectOpportunity): boolean {
  return /preview|illustrative|not verified|not connected|not supplied/i.test(
    `${item.status} ${item.context}`,
  );
}

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
        <div className={styles.heading}>
          <span className={styles.eyebrow}>
            Project preview opportunities
          </span>

          <h2 id="project-inventory-title">
            Explore individual opportunities.
          </h2>

          <p>
            These records are experience previews, not live inventory.
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
          {opportunities.map((item) => {
            const preview = isPreviewOpportunity(item);

            return (
              <article key={item.id} className={styles.card}>
                <div className={styles.media} aria-hidden="true">
                  <span className={styles.mediaLabel}>
                    {preview
                      ? "ILLUSTRATIVE · PREVIEW ONLY"
                      : "PROJECT OPPORTUNITY"}
                  </span>

                  <strong className={styles.configuration}>
                    {preview
                      ? "Example configuration"
                      : item.configuration}
                  </strong>

                  <span className={styles.mediaMark}>H</span>
                </div>

                <div className={styles.body}>
                  <span className={styles.status}>
                    {preview ? "Experience preview" : item.status}
                  </span>

                  <h3>
                    {preview
                      ? "Illustrative property opportunity"
                      : item.title}
                  </h3>

                  <p>
                    {preview
                      ? "Demonstration content only. No live offer or availability is represented."
                      : item.context}
                  </p>

                  <div className={styles.meta}>
                    <div>
                      <span>Displayed value</span>
                      <strong>
                        {preview ? "Preview only" : item.price}
                      </strong>
                    </div>

                    <div>
                      <span>Area</span>
                      <strong>
                        {preview ? "Preview only" : item.area}
                      </strong>
                    </div>
                  </div>

                  {item.href ? (
                    <Link href={item.href} className={styles.action}>
                      Open property preview
                      <span aria-hidden="true">→</span>
                    </Link>
                  ) : (
                    <span className={styles.disabledAction}>
                      Preview only · no property link
                    </span>
                  )}
                </div>
              </article>
            );
          })}
        </div>
      ) : (
        <p className={styles.emptyState}>
          No project opportunity records are connected to this preview.
          Confirmed opportunities will appear when an approved source
          provides them. No placeholder inventory has been generated.
        </p>
      )}
    </section>
  );
}
