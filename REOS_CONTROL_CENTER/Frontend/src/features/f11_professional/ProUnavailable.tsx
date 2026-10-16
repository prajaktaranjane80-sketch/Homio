
import type { ProSection } from "./pro.types";
import {
  PRO_CAPABILITIES,
  PRO_SECTION_META,
} from "./pro.types";
import styles from "./ProWorkspace.module.css";

type ProCapabilityKey = keyof typeof PRO_CAPABILITIES;

type ProUnavailableProps = Readonly<{
  section: Exclude<ProSection, "dashboard">;
  capabilityKey: ProCapabilityKey;
  title: string;
  description: string;
  detail: string;
}>;

export default function ProUnavailable({
  section,
  capabilityKey,
  title,
  description,
  detail,
}: ProUnavailableProps) {
  const meta = PRO_SECTION_META[section];
  const capabilityConnected = PRO_CAPABILITIES[capabilityKey];

  return (
    <>
      <section
        className={styles.emptyState}
        aria-labelledby="pro-unavailable-title"
      >
        <div className={styles.emptyIcon} aria-hidden="true">
          ◇
        </div>

        <p className={styles.emptyEyebrow}>
          {capabilityConnected
            ? "RECORD AUTHORIZATION REQUIRED"
            : "SERVICE NOT CONNECTED"}
        </p>

        <h2
          id="pro-unavailable-title"
          className={styles.emptyTitle}
        >
          {title}
        </h2>

        <p className={styles.emptyDescription}>
          {description}
        </p>

        <p className={styles.emptyDisclosure}>
          {detail}
        </p>
      </section>

      <section
        className={styles.panelGrid}
        aria-label={`${meta.title} integration status`}
      >
        <article className={styles.panel}>
          <header className={styles.panelHeader}>
            <div>
              <h3 className={styles.panelTitle}>Role access</h3>
              <p className={styles.panelDescription}>
                Server-side authorization
              </p>
            </div>
          </header>

          <div className={styles.fieldRow}>
            <span className={styles.fieldLabel}>Professional role</span>
            <strong className={styles.fieldValue}>Not verified</strong>
          </div>

          <div className={styles.fieldRow}>
            <span className={styles.fieldLabel}>Record permission</span>
            <strong className={styles.fieldValue}>Not granted</strong>
          </div>
        </article>

        <article className={styles.panel}>
          <header className={styles.panelHeader}>
            <div>
              <h3 className={styles.panelTitle}>Data connection</h3>
              <p className={styles.panelDescription}>
                Approved REOS capability
              </p>
            </div>
          </header>

          <div className={styles.fieldRow}>
            <span className={styles.fieldLabel}>Source</span>
            <strong className={styles.fieldValue}>
              {capabilityConnected
                ? "Configured; record still unavailable"
                : "Not connected"}
            </strong>
          </div>

          <div className={styles.fieldRow}>
            <span className={styles.fieldLabel}>Preview records</span>
            <strong className={styles.fieldValue}>None displayed</strong>
          </div>
        </article>
      </section>
    </>
  );
}
