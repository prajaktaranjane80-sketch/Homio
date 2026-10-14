import styles from "./MyHomio.module.css";

const DOCUMENT_TYPES = [
  {
    title: "Property information",
    description:
      "Property packs and listing documents supplied through an authorized source.",
  },
  {
    title: "Project documentation",
    description:
      "Project information and approved files associated with a real project record.",
  },
  {
    title: "Transaction documents",
    description:
      "Agreements and transaction documents only when an approved secure workflow provides them.",
  },
];

export default function MyHomioDocuments() {
  return (
    <>
      <header className={styles.panelHeader}>
        <p className={styles.kicker}>PRIVATE DOCUMENT SPACE</p>

        <h2 className={styles.panelTitle}>Documents</h2>

        <p className={styles.panelLead}>
          An account document workspace must preserve the link between a file,
          its source, the user&apos;s authorization and the property or workflow
          it belongs to.
        </p>
      </header>

      <div className={styles.featureCard}>
        <div className={styles.featureHead}>
          <h3 className={styles.featureTitle}>Secure document repository</h3>
          <span className={styles.statusBadge}>Not connected</span>
        </div>

        <p className={styles.featureText}>
          No authorized document repository is connected to this screen.
          File upload, private download links, sharing permissions and
          document deletion are therefore not enabled.
        </p>
      </div>

      <div className={styles.sectionHeading}>
        <div>
          <h3>Document categories</h3>
          <p>Supported information categories, not files currently stored.</p>
        </div>
      </div>

      <div className={styles.contentGrid}>
        {DOCUMENT_TYPES.map((document) => (
          <article className={styles.featureCard} key={document.title}>
            <div className={styles.featureHead}>
              <h3 className={styles.featureTitle}>{document.title}</h3>
              <span className={styles.navIcon} aria-hidden="true">DC</span>
            </div>
            <p className={styles.featureText}>{document.description}</p>
          </article>
        ))}
      </div>

      <div className={styles.notice}>
        Do not submit identity, financial or transaction documents into an
        unconnected UI. Document access must be protected by the authorized
        document service—not by a visible link alone.
      </div>
    </>
  );
}
