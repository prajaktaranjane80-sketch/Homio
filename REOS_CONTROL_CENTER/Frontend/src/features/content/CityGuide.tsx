import type { ContentSection } from "./ContentExperience.types";
import styles from "./ContentExperience.module.css";

type Props = Readonly<{
  city: string;
  country: string;
  introduction: string;
  sections: readonly ContentSection[];
  sourceDisclosure: string;
}>;

export default function CityGuide({
  city,
  country,
  introduction,
  sections,
  sourceDisclosure,
}: Props) {
  return (
    <article className={styles.contentArticle}>
      <header className={styles.contentArticleHeader}>
        <span className={styles.contentEyebrow}>CITY GUIDE</span>
        <h1 className={styles.contentTitle}>{city}</h1>
        <p className={styles.contentDescription}>{country} · {introduction}</p>
      </header>
      <div className={styles.contentArticleBody}>
        {sections.map((section) => (
          <section className={styles.contentSection} key={section.id}>
            <h2>{section.title}</h2>
            <p>{section.body}</p>
          </section>
        ))}
      </div>
      <p className={styles.contentDisclosure}>{sourceDisclosure}</p>
    </article>
  );
}
