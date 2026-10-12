import styles from "./PropertyAI.module.css";

const prompts = [
  "What should I know before enquiring?",
  "How does this property compare with another one?",
  "Help me understand the location.",
];

export default function PropertyAI() {
  return (
    <section
      id="property-ai"
      className={styles.section}
      aria-labelledby="property-ai-heading"
    >
      <div className={styles.header}>
        <div>
          <span className={styles.eyebrow}>HOMIO AI PREVIEW</span>
          <h2 id="property-ai-heading">
            Get context before you decide.
          </h2>
          <p>
            These are example question topics, not generated answers.
            The connected AI capability is not available on this page yet.
          </p>
        </div>

        <span className={styles.badge}>AI NOT CONNECTED</span>
      </div>

      <div className={styles.promptGrid}>
        {prompts.map((prompt) => (
          <button
            key={prompt}
            type="button"
            className={styles.prompt}
            disabled
            aria-disabled="true"
            title="An answer cannot be generated until the approved AI capability is connected."
            style={{ opacity: 0.62, cursor: "not-allowed" }}
          >
            <span>{prompt}</span>
            <strong aria-hidden="true">→</strong>
          </button>
        ))}
      </div>

      <p
        style={{
          margin: "12px 0 0",
          color: "#667085",
          fontSize: 11,
          lineHeight: 1.6,
        }}
      >
        No AI request was sent and no answer was generated. Property facts
        must come from authoritative data; frontend copy cannot verify them.
      </p>
    </section>
  );
}
