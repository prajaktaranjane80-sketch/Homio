import type { ReactNode } from "react";

import styles from "./ContentExperience.module.css";

type Props = Readonly<{
  title: string;
  category: string;
  summary: string;
  publishedAt?: string;
  sourceDisclosure: string;
  children: ReactNode;
}>;

export default function AdviceArticle({
  title,
  category,
  summary,
  publishedAt,
  sourceDisclosure,
  children,
}: Props) {
  return (
    <article className={styles.contentArticle}>
      <header className={styles.contentArticleHeader}>
        <span className={styles.contentEyebrow}>{category}</span>
        <h1 className={styles.contentTitle}>{title}</h1>
        <p className={styles.contentDescription}>{summary}</p>
        {publishedAt ? (
          <p className={styles.contentCardDescription}>Published: {publishedAt}</p>
        ) : null}
      </header>
      <div className={styles.contentArticleBody}>{children}</div>
      <p className={styles.contentDisclosure}>{sourceDisclosure}</p>
    </article>
  );
}
