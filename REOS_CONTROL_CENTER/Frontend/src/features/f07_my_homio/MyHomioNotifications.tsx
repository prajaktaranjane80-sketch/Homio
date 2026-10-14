import styles from "./MyHomio.module.css";

const NOTIFICATION_CATEGORIES = [
  {
    title: "Search and listing updates",
    description:
      "Relevant updates based on a saved requirement, once alert delivery is connected.",
  },
  {
    title: "Enquiry and conversation updates",
    description:
      "A response or message reported by an authorized enquiry or messaging service.",
  },
  {
    title: "Visit and journey updates",
    description:
      "Appointment changes or workflow events reported by the responsible service.",
  },
];

export default function MyHomioNotifications() {
  return (
    <>
      <header className={styles.panelHeader}>
        <p className={styles.kicker}>ACCOUNT SIGNALS</p>

        <h2 className={styles.panelTitle}>Notifications</h2>

        <p className={styles.panelLead}>
          Important account events should be actionable, time-stamped and
          connected to the source record that triggered them—not generic
          marketing noise.
        </p>
      </header>

      <div className={styles.featureCard}>
        <div className={styles.featureHead}>
          <h3 className={styles.featureTitle}>Notification feed</h3>
          <span className={styles.statusBadge}>Not connected</span>
        </div>

        <p className={styles.featureText}>
          No authorized notification feed or unread-count service is available
          here. This page will not invent alerts, mark messages as read or
          suggest a property event has occurred.
        </p>
      </div>

      <div className={styles.sectionHeading}>
        <div>
          <h3>Event categories</h3>
          <p>Supported notification types, not active user alerts.</p>
        </div>
      </div>

      <div className={styles.contentGrid}>
        {NOTIFICATION_CATEGORIES.map((category) => (
          <article className={styles.featureCard} key={category.title}>
            <h3 className={styles.featureTitle}>{category.title}</h3>
            <p className={styles.featureText}>{category.description}</p>
          </article>
        ))}
      </div>

      <div className={styles.notice}>
        Notification preferences and delivery are not persisted in this
        account view yet. The section remains informational until the
        notification service is integrated.
      </div>
    </>
  );
}
