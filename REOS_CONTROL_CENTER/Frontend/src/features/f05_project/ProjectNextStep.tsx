import Link from "next/link";

import type { ProjectRecord } from "./project.types";
import styles from "./ProjectNextStep.module.css";

type ProjectNextStepProps = Readonly<{
  project: ProjectRecord;
}>;

export default function ProjectNextStep({
  project,
}: ProjectNextStepProps) {
  return (
    <section
      className={styles.section}
      id="next-step"
      aria-labelledby="project-next-step-heading"
    >
      <div>
        <span className={styles.eyebrow}>NEXT STEP</span>

        <h2 id="project-next-step-heading">
          Ready to move from project discovery to a property?
        </h2>

        <p>
          Continue from {project.name} to another project or collection
          preview. Project facts and opportunity availability remain
          non-authoritative until connected to the approved source.
        </p>
      </div>

      <div className={styles.actions}>
        <Link href="#inventory" className={styles.primary}>
          Review opportunities
        </Link>

        <Link
          href="/search?intent=projects"
          className={styles.secondary}
        >
          Continue project discovery
        </Link>
      </div>
    </section>
  );
}
