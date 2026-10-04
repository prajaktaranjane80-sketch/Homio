import styles from "./AIConversationPreview.module.css";

const context = [
  "Your search intent",
  "Selected locations",
  "Saved properties",
  "Market context",
];

export default function AIConversationPreview() {
  return (
    <div className={styles.panel}>
      <div className={styles.header}>
        <div className={styles.mark}>H</div>

        <div>
          <strong>HOMIO AI</strong>
          <span>Property discovery assistant</span>
        </div>

        <span className={styles.ready}>
          <i />
          Ready
        </span>
      </div>

      <div className={styles.messages}>
        <div className={`${styles.message} ${styles.user}`}>
          I want a premium 2-bedroom home close to the city.
        </div>

        <div className={`${styles.message} ${styles.ai}`}>
          I can help narrow that down. I can compare locations, property
          types, projects and price context before you decide what to enquire
          about.
        </div>

        <div className={styles.context}>
          <span>Working with your context</span>

          <div>
            {context.map((item) => (
              <span key={item}>✓ {item}</span>
            ))}
          </div>
        </div>
      </div>

      <div className={styles.input}>
        <span>Ask HOMIO anything about this search...</span>
        <button type="button" aria-label="Open HOMIO AI">
          →
        </button>
      </div>
    </div>
  );
}
