import Link from "next/link";

import ProjectActions from "./ProjectActions";
import ProjectAmenities from "./ProjectAmenities";
import ProjectFacts from "./ProjectFacts";
import ProjectGallery from "./ProjectGallery";
import ProjectInventory from "./ProjectInventory";
import ProjectInventorySummary from "./ProjectInventorySummary";
import ProjectLocation from "./ProjectLocation";
import ProjectNextStep from "./ProjectNextStep";
import RelatedProjects from "./RelatedProjects";
import ProjectSummary from "./ProjectSummary";
import ProjectTrust from "./ProjectTrust";
import type { ProjectRecord } from "./project.types";

import styles from "./ProjectPage.module.css";

type ProjectPageProps = Readonly<{
  project: ProjectRecord;
}>;

export default function ProjectPage({
  project,
}: ProjectPageProps) {
  return (
    <main className={styles.page}>
      <div className="homio-container">
        <nav
          className={styles.breadcrumbs}
          aria-label="Breadcrumb"
        >
          <Link href="/">HOMIO</Link>
          <span aria-hidden="true">›</span>
          <Link href="/search">Search</Link>
          <span aria-hidden="true">›</span>
          <span>{project.shortName}</span>
        </nav>

        <div className={styles.heroGrid}>
          <ProjectGallery media={project.media} />

          <aside className={styles.summaryColumn}>
            <ProjectSummary project={project} />
            <ProjectActions project={project} />
          </aside>
        </div>

        <section className={styles.collectionContext}>
          <span className={styles.eyebrow}>
            PROJECT & COLLECTION
          </span>

          <div className={styles.collectionContent}>
            <div>
              <h2>
                {project.collectionName ??
                  "Explore the wider opportunity."}
              </h2>

              <p>
                Move from one property into the wider project context,
                then return to individual opportunities without losing
                your discovery path.
              </p>
            </div>

            <Link
              href="#inventory"
              className={styles.contextLink}
            >
              Explore opportunities →
            </Link>
          </div>
        </section>

        <ProjectFacts project={project} />

        <ProjectInventorySummary
          summary={project.inventorySummary}
        />

        <ProjectInventory
          projectId={project.id}
          opportunities={project.opportunities}
        />

        <ProjectAmenities project={project} />

        <ProjectLocation project={project} />

        <ProjectTrust project={project} />

        <RelatedProjects project={project} />

        <ProjectNextStep project={project} />
      </div>
    </main>
  );
}
