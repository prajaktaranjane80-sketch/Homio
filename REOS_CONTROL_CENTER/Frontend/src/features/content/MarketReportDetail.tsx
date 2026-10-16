import styles from "./ContentExperience.module.css";
import type { ContentSection, MarketReportRecord } from "./ContentExperience.types";

type Props = Readonly<{
  report: MarketReportRecord;
  sections: readonly ContentSection[];
}>;

export default function MarketReportDetail({ report, sections }: Props) {
  return (
    <article className={styles.contentArticle}>
      <header className={styles.contentArticleHeader}>
        <span className={styles.contentEyebrow}>MARKET REPORT · {report.marketName}</span>
        <h1 className={styles.contentTitle}>{report.title}</h1>
        <p className={styles.contentDescription}>{report.description}</p>
        <span
          className={`${styles.contentStatus} ${
            report.state === "published"
              ? styles.contentStatusPublished
              : styles.contentStatusPreview
          }`}
        >
          {report.state === "published" ? "PUBLISHED SOURCE" : report.state.toUpperCase()}
        </span>
        {report.periodLabel ? (
          <p className={styles.contentCardDescription}>Reporting period: {report.periodLabel}</p>
        ) : null}
        {report.sourceName ? (
          <p className={styles.contentCardDescription}>Source: {report.sourceName}</p>
        ) : null}
      </header>

      {report.state === "unavailable" ? (
        <p className={styles.contentDisclosure}>
          This report is unavailable. Its content must not be inferred from the title or market name.
        </p>
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
    </article>
  );
}
