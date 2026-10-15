import Link from "next/link";

import type { ProjectRecord } from "./project.types";
import styles from "./ProjectNextStep.module.css";

type ProjectNextStepProps = Readonly<{
  project: ProjectRecord;
}>;

export default function ProjectNextStep({ project }: ProjectNextStepProps) {
  const enquiryHref =
    "/enquiry?kind=project&id=" +
    encodeURIComponent(project.id) +
    "&mode=enquiry";

  const visitHref =
    "/enquiry?kind=project&id=" +
    encodeURIComponent(project.id) +
    "&mode=visit";

  return (
    <section
      className={styles.section}
      id="next-step"
      aria-labelledby="project-next-step-heading"
    >
      <div>
        <span className={styles.eyebrow}>NEXT STEP PREVIEW</span>

        <h2 id="project-next-step-heading">
          Want to ask about this project or plan a visit?
        </h2>

        <p>
          Prepare a project enquiry or visit-request draft. Submission,
          developer or broker notification, availability checks and booking
          confirmation require connected authorized services, which are not
          available in this preview.
        </p>
      </div>

      <div className={styles.actions}>
        <Link href={enquiryHref} className={styles.primary}>
          Prepare enquiry draft
        </Link>

        <Link href={visitHref} className={styles.secondary}>
          Prepare visit request
        </Link>
      </div>

      <p className={styles.continueLinks}>
        Also: <Link href="#inventory">review opportunities</Link> or{" "}
        <Link href="/search?intent=projects">Continue project discovery</Link>.
      </p>
    </section>
  );
}
