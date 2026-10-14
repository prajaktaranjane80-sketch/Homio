import styles from "./MyHomio.module.css";

export default function MyHomioConversations() {
  return (
    <>
      <header className={styles.panelHeader}>
        <p className={styles.kicker}>PRIVATE INBOX</p>

        <h2 className={styles.panelTitle}>Conversations</h2>

        <p className={styles.panelLead}>
          A single inbox for connected conversations with the parties involved
          in your property journey, with context and response timing.
        </p>
      </header>

      <section className={styles.featureCard} aria-label="Inbox connection state">
        <div className={styles.featureHead}>
          <div>
            <p className={styles.kicker}>INBOX STATUS</p>
            <h3 className={styles.featureTitle}>Conversation feed unavailable</h3>
          </div>
          <span className={styles.statusBadge}>Not connected</span>
        </div>

        <p className={styles.featureText}>
          This workspace is not receiving messages from an authorized
          conversation service. Message previews, read state, sender identity,
          attachment links and unread totals will remain absent until real data
          is supplied.
        </p>
      </section>

      <div className={styles.sectionHeading}>
        <div>
          <h3>What the connected inbox will include</h3>
          <p>These are capability definitions—not sample conversations.</p>
        </div>
      </div>

      <div className={styles.contentGrid}>
        <article className={styles.featureCard}>
          <h3 className={styles.featureTitle}>Property context</h3>
          <p className={styles.featureText}>
            Each conversation will reference a real property, project or
            enquiry when that reference is present in the source record.
          </p>
        </article>

        <article className={styles.featureCard}>
          <h3 className={styles.featureTitle}>Verified message state</h3>
          <p className={styles.featureText}>
            Sender, time, delivery and read status must come from the
            authorized messaging service. HOMIO will not infer that a reply
            was sent or read.
          </p>
        </article>
      </div>
    </>
  );
}
