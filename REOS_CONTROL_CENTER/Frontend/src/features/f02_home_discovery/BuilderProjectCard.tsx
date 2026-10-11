import Link from "next/link";
import styles from "./BuilderProjectCard.module.css";

export type BuilderProjectCardData = {
  name: string;
  focus: string;
  projects: string;
  href: string;
  image: string;
};

type Props = {
  project: BuilderProjectCardData;
};

export default function BuilderProjectCard({ project }: Props) {
  return (
    <Link href={project.href} className={styles.card}>
      <div className={styles.imageWrap}>
        <img
          src={project.image}
          alt={project.name}
          className={styles.image}
          loading="lazy"
        />

        <span className={styles.projectCount}>{project.projects}</span>
      </div>

      <div className={styles.body}>
        <span className={styles.label}>BUILDER PROFILE</span>

        <h3>{project.name}</h3>

        <p>{project.focus}</p>

        <span className={styles.action}>
          View projects
          <span aria-hidden="true">→</span>
        </span>
      </div>
    </Link>
  );
}
