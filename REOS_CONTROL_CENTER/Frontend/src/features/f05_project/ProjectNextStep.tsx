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
    >
      <div>
        <span className={styles.eyebrow}>
          NEXT STEP
        </span>

        <h2>
          Ready to move from project discovery to a property?
        </h2>

        <p>
          {project.name} is designed as a connected discovery layer.
          Open an available opportunity where a verified property reference
          exists, or continue exploring the market.
        </p>
      </div>

      <div className={styles.actions}>
        <Link
          href="#inventory"
          className={styles.primary}
        >
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
