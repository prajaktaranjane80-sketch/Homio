
import type { ReactNode } from "react";

import type { ProSection } from "./pro.types";
import { PRO_SECTION_META } from "./pro.types";
import styles from "./ProWorkspace.module.css";

type ProWorkspaceProps = Readonly<{
  section: ProSection;
  children: ReactNode;
}>;

export default function ProWorkspace({
  section,
  children,
}: ProWorkspaceProps) {
  const meta = PRO_SECTION_META[section];

  return (
    <section className={styles.page} aria-labelledby="pro-page-title">
      <header className={styles.pageHeading}>
        <div className={styles.headingCopy}>
          <p className={styles.pageEyebrow}>{meta.eyebrow}</p>

          <h1 id="pro-page-title" className={styles.pageTitle}>
            {meta.title}
          </h1>

          <p className={styles.pageDescription}>{meta.description}</p>
        </div>

        <div className={styles.pageStatus}>
          <span className={styles.pageStatusDot} aria-hidden="true" />
          SERVICE PREVIEW
        </div>
      </header>

      {children}
    </section>
  );
}
