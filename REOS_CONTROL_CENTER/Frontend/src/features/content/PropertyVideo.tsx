import styles from "./ContentExperience.module.css";

type Props = Readonly<{
  title: string;
  description: string;
  sourceDisclosure: string;
  videoUrl?: string;
  posterUrl?: string;
}>;

export default function PropertyVideo({
  title,
  description,
  sourceDisclosure,
  videoUrl,
  posterUrl,
}: Props) {
  return (
    <section className={styles.contentRoot}>
      <header className={styles.contentHeader}>
        <span className={styles.contentEyebrow}>PROPERTY MEDIA</span>
        <h1 className={styles.contentTitle}>{title}</h1>
        <p className={styles.contentDescription}>{description}</p>
      </header>

      {videoUrl ? (
        <div className={styles.contentVideo}>
          <video
            controls
            preload="metadata"
            src={videoUrl}
            poster={posterUrl}
            aria-label={title}
          >
            Your browser does not support embedded video.
          </video>
          <p className={styles.contentVideoCaption}>{sourceDisclosure}</p>
        </div>
      ) : (
        <div className={styles.contentEmpty}>
          Video media is not connected. No placeholder clip is presented as a real property walkthrough.
        </div>
      )}
    </section>
  );
}
