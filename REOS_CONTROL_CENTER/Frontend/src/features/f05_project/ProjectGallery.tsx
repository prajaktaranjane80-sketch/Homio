import type { ProjectMedia } from "./project.types";

import styles from "./ProjectGallery.module.css";

type ProjectGalleryProps = Readonly<{
  media: ProjectMedia[];
}>;

export default function ProjectGallery({
  media,
}: ProjectGalleryProps) {
  const featured = media[0];
  const secondary = media.slice(1, 5);

  return (
    <section
      className={styles.wrapper}
      aria-label="Project media"
    >
      <div className={styles.main}>
        <div
          className={styles.mainVisual}
          role="img"
          aria-label={
            featured?.label ?? "Project visual preview"
          }
        >
          <div className={styles.visualOverlay}>
            <span>HOMIO PROJECT</span>
            <strong>
              {featured?.label ?? "Project overview"}
            </strong>
          </div>
        </div>
      </div>

      <div className={styles.grid}>
        {secondary.map((item) => (
          <div
            key={item.id}
            className={styles.tile}
            role="img"
            aria-label={item.label}
          >
            <span>{item.label}</span>
          </div>
        ))}
      </div>

      <div className={styles.notice}>
        Project media shown here is experience-preview content.
      </div>
    </section>
  );
}
