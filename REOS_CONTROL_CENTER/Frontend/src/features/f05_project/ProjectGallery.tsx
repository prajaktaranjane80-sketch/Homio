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
      aria-label="Project media preview"
    >
      <div className={styles.main}>
        <div
          className={styles.mainVisual}
          role="img"
          aria-label={
            featured
              ? `Illustrative media placeholder for ${featured.label}; actual verified project media is not connected`
              : "Project media not supplied"
          }
        >
          <div className={styles.visualOverlay}>
            <span>PROJECT MEDIA PREVIEW · NOT A VERIFIED ASSET</span>
            <strong>
              {featured?.label ?? "Project media not supplied"}
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
            aria-label={`Illustrative placeholder: ${item.label}. Actual media is not connected.`}
          >
            <span>{item.label} · preview placeholder</span>
          </div>
        ))}
      </div>

      <div className={styles.notice}>
        Project media shown here is experience-preview content.
        Actual project images, master plans, video and virtual tours
        have not been supplied by the current data source.
      </div>
    </section>
  );
}
