import type { ContentSection } from "./ContentExperience.types";
import styles from "./ContentExperience.module.css";

type Props = Readonly<{
  title: string;
  jurisdiction: string;
  overview: string;
  sections: readonly ContentSection[];
  sourceDisclosure: string;
  updatedAt?: string;
}>;

export default function LegalGuide({
  title,
  jurisdiction,
  overview,
  sections,
  sourceDisclosure,
  updatedAt,
}: Props) {
  return (
    <article className={styles.contentArticle}>
      <header className={styles.contentArticleHeader}>
        <span className={styles.contentEyebrow}>PROPERTY LEGAL GUIDE</span>
        <h1 className={styles.contentTitle}>{title}</h1>
        <p className={styles.contentDescription}>{overview}</p>
        <p className={styles.contentCardDescription}>Jurisdiction: {jurisdiction}</p>
        {updatedAt ? <p className={styles.contentCardDescription}>Updated: {updatedAt}</p> : null}
      </header>
      <div className={styles.contentArticleBody}>
        {sections.map((section) => (
          <section className={styles.contentSection} key={section.id}>
            <h2>{section.title}</h2>
            <p>{section.body}</p>
          </section>
        ))}
      </div>
      <p className={styles.contentDisclosure}>
        {sourceDisclosure} This material is informational and is not a substitute for qualified legal advice in the relevant jurisdiction.
      </p>
    </article>
  );
}
