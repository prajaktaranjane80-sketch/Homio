import type { ContentSection } from "./ContentExperience.types";
import styles from "./ContentExperience.module.css";

type Props = Readonly<{
  projectName: string;
  marketName: string;
  overview: string;
  sections: readonly ContentSection[];
  sourceDisclosure: string;
  state: "published" | "preview" | "unavailable";
}>;

export default function ProjectGuide({
  projectName,
  marketName,
  overview,
  sections,
  sourceDisclosure,
  state,
}: Props) {
  return (
    <article className={styles.contentArticle}>
      <header className={styles.contentArticleHeader}>
        <span className={styles.contentEyebrow}>PROJECT GUIDE · {marketName}</span>
        <h1 className={styles.contentTitle}>{projectName}</h1>
        <p className={styles.contentDescription}>{overview}</p>
        <span className={`${styles.contentStatus} ${state === "published" ? styles.contentStatusPublished : styles.contentStatusPreview}`}>
          {state.toUpperCase()}
        </span>
      </header>

      {state === "unavailable" ? (
        <p className={styles.contentEmpty}>Verified project information is not available.</p>
      ) : (
        <div className={styles.contentArticleBody}>
          {sections.map((section) => (
            <section className={styles.contentSection} key={section.id}>
              <h2>{section.title}</h2>
              <p>{section.body}</p>
            </section>
          ))}
        </div>
      )}
      <p className={styles.contentDisclosure}>{sourceDisclosure}</p>
    </article>
  );
}
