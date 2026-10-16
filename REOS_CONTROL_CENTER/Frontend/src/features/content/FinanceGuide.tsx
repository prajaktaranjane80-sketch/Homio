import type { ContentSection } from "./ContentExperience.types";
import styles from "./ContentExperience.module.css";

type Props = Readonly<{
  title: string;
  overview: string;
  sections: readonly ContentSection[];
  sourceDisclosure: string;
  updatedAt?: string;
}>;

export default function FinanceGuide({
  title,
  overview,
  sections,
  sourceDisclosure,
  updatedAt,
}: Props) {
  return (
    <article className={styles.contentArticle}>
      <header className={styles.contentArticleHeader}>
        <span className={styles.contentEyebrow}>PROPERTY FINANCE GUIDE</span>
        <h1 className={styles.contentTitle}>{title}</h1>
        <p className={styles.contentDescription}>{overview}</p>
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
        {sourceDisclosure} This guide is educational and is not personal financial or lending advice.
      </p>
    </article>
  );
}
