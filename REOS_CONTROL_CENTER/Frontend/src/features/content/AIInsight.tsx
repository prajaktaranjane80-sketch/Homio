import styles from "./ContentExperience.module.css";

type Props = Readonly<{
  title: string;
  summary?: string;
  insights?: readonly string[];
  updatedAt?: string;
  sourceDisclosure: string;
  state: "verified_source" | "preview" | "unavailable";
}>;

export default function AIInsight({
  title,
  summary,
  insights = [],
  updatedAt,
  sourceDisclosure,
  state,
}: Props) {
  const available = state === "verified_source";

  return (
    <article className={styles.contentArticle}>
      <header className={styles.contentArticleHeader}>
        <span className={styles.contentEyebrow}>HOMIO AI INSIGHT</span>
        <h1 className={styles.contentTitle}>{title}</h1>
        <span className={`${styles.contentStatus} ${available ? styles.contentStatusPublished : styles.contentStatusPreview}`}>
          {available ? "SOURCE PROVIDED" : state === "preview" ? "PREVIEW" : "UNAVAILABLE"}
        </span>
        {summary ? <p className={styles.contentDescription}>{summary}</p> : null}
        {updatedAt ? <p className={styles.contentCardDescription}>Source updated: {updatedAt}</p> : null}
      </header>

      {!available || insights.length === 0 ? (
        <p className={styles.contentEmpty}>
          No source-backed AI insights are available to display.
        </p>
      ) : (
        <ul className={styles.contentArticleBody}>
          {insights.map((insight, index) => (
            <li key={`${index}-${insight.slice(0, 36)}`}>{insight}</li>
          ))}
        </ul>
      )}

      <p className={styles.contentDisclosure}>{sourceDisclosure}</p>
    </article>
  );
}
