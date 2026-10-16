import type { ContentSection } from "./ContentExperience.types";
import styles from "./ContentExperience.module.css";

type Props = Readonly<{
  locality: string;
  city: string;
  country: string;
  state: "published" | "preview" | "unavailable";
  sections: readonly ContentSection[];
  sourceDisclosure: string;
}>;

export default function LocalityReport({
  locality,
  city,
  country,
  state,
  sections,
  sourceDisclosure,
}: Props) {
  return (
    <article className={styles.contentArticle}>
      <header className={styles.contentArticleHeader}>
        <span className={styles.contentEyebrow}>LOCALITY CONTEXT</span>
        <h1 className={styles.contentTitle}>{locality}</h1>
        <p className={styles.contentDescription}>{city}, {country}</p>
        <span className={`${styles.contentStatus} ${state === "published" ? styles.contentStatusPublished : styles.contentStatusPreview}`}>
          {state.toUpperCase()}
        </span>
      </header>

      {state === "unavailable" ? (
        <p className={styles.contentEmpty}>Locality data is unavailable from a trusted source.</p>
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
