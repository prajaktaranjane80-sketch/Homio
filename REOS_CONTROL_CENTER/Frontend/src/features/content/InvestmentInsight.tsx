import type { ContentSection } from "./ContentExperience.types";
import styles from "./ContentExperience.module.css";

type Props = Readonly<{
  title: string;
  marketName: string;
  overview: string;
  sections: readonly ContentSection[];
  sourceDisclosure: string;
  dataState: "verified" | "preview" | "unavailable";
}>;

export default function InvestmentInsight({
  title,
  marketName,
  overview,
  sections,
  sourceDisclosure,
  dataState,
}: Props) {
  return (
    <article className={styles.contentArticle}>
      <header className={styles.contentArticleHeader}>
        <span className={styles.contentEyebrow}>INVESTMENT CONTEXT · {marketName}</span>
        <h1 className={styles.contentTitle}>{title}</h1>
        <p className={styles.contentDescription}>{overview}</p>
        <span className={`${styles.contentStatus} ${dataState === "verified" ? styles.contentStatusPublished : styles.contentStatusPreview}`}>
          {dataState === "verified" ? "SOURCE VERIFIED" : dataState.toUpperCase()}
        </span>
      </header>

      {dataState === "unavailable" ? (
        <p className={styles.contentEmpty}>Investment data is not available from a verified source.</p>
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
      <p className={styles.contentDisclosure}>
        {sourceDisclosure} This is informational content, not a guarantee of returns or a personal investment recommendation.
      </p>
    </article>
  );
}
