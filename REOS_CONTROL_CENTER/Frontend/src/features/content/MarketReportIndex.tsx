import Link from "next/link";

import styles from "./ContentExperience.module.css";
import type { MarketReportRecord } from "./ContentExperience.types";

type Props = Readonly<{
  reports: readonly MarketReportRecord[];
}>;

export default function MarketReportIndex({ reports }: Props) {
  return (
    <section className={styles.contentRoot}>
      <header className={styles.contentHeader}>
        <span className={styles.contentEyebrow}>MARKET INTELLIGENCE</span>
        <h1 className={styles.contentTitle}>Market reports</h1>
        <p className={styles.contentDescription}>
          Market insights should identify their coverage period and source.
          Unverified forecasts and invented statistics are not displayed.
        </p>
      </header>

      {reports.length === 0 ? (
        <div className={styles.contentEmpty}>
          Market reports are not connected. There is no verified report data to display.
        </div>
      ) : (
        <div className={styles.contentGrid}>
          {reports.map((report) => (
            <Link className={styles.contentCard} key={report.id} href={report.href}>
              <span
                className={`${styles.contentStatus} ${
                  report.state === "published"
                    ? styles.contentStatusPublished
                    : styles.contentStatusPreview
                }`}
              >
                {report.state === "published"
                  ? "PUBLISHED"
                  : report.state === "preview"
                    ? "PREVIEW"
                    : "UNAVAILABLE"}
              </span>
              <h2 className={styles.contentCardTitle}>{report.title}</h2>
              <p className={styles.contentCardDescription}>{report.description}</p>
              <p className={styles.contentCardDescription}>
                {report.marketName}
                {report.periodLabel ? ` · ${report.periodLabel}` : ""}
              </p>
              <span className={styles.contentCardFooter}>View report <span aria-hidden="true">↗</span></span>
            </Link>
          ))}
        </div>
      )}
    </section>
  );
}
