import Link from "next/link";
import styles from "./HomioAISection.module.css";

const suggestions = [
  "Compare two homes",
  "Find family-friendly areas",
  "Explain this market",
  "Refine my property search",
];

const contextItems = [
  "Your search intent",
  "Selected locations",
  "Saved properties",
  "Market context",
];

export default function HomioAISection() {
  return (
    <section id="homio-ai" className={styles.section}>
      <div className="homio-container">
        <div className={styles.shell}>
          <div className={styles.content}>
            <span className={styles.eyebrow}>HOMIO AI</span>

            <h2>
              Search less.
              <br />
              Understand more.
            </h2>

            <p>
              HOMIO AI helps turn a property search into a conversation.
              Refine what you want, ask questions about a property or market,
              and move toward the next useful action.
            </p>

            <div className={styles.actions}>
              <Link href="/ai" className={styles.primary}>
                Open HOMIO AI
                <span aria-hidden="true">↗</span>
              </Link>

              <Link href="/search" className={styles.secondary}>
                Continue normal search
              </Link>
            </div>

            <div className={styles.suggestions}>
              <span className={styles.suggestionLabel}>TRY ASKING</span>

              <div className={styles.chips}>
                {suggestions.map((suggestion) => (
                  <Link key={suggestion} href={`/ai?q=${encodeURIComponent(suggestion)}`}>
                    {suggestion}
                  </Link>
                ))}
              </div>
            </div>
          </div>

          <div className={styles.aiPanel}>
            <div className={styles.panelHeader}>
              <div className={styles.aiMark}>H</div>

              <div>
                <strong>HOMIO AI</strong>
                <span>Property discovery assistant</span>
              </div>

              <span className={styles.live} aria-label="AI available">
                <span />
                Ready
              </span>
            </div>

            <div className={styles.messages}>
              <div className={`${styles.message} ${styles.userMessage}`}>
                I want a premium 2-bedroom home close to the city.
              </div>

              <div className={`${styles.message} ${styles.aiMessage}`}>
                I can help narrow that down. I can compare locations, property
                types, projects and price context before you decide what to
                enquire about.
              </div>

              <div className={styles.contextBox}>
                <span>Working with your context</span>

                <div className={styles.contextGrid}>
                  {contextItems.map((item) => (
                    <div key={item}>
                      <span className={styles.contextCheck}>✓</span>
                      {item}
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className={styles.input}>
              <span>Ask HOMIO anything about this search...</span>

              <button type="button" aria-label="Start AI conversation">
                →
              </button>
            </div>
          </div>
        </div>

        <div className={styles.bottom}>
          <span>
            <strong>AI supports the journey.</strong> HOMIO brokerage remains
            the action layer when you are ready.
          </span>

          <Link href="/ai">Explore AI experience</Link>
        </div>
      </div>
    </section>
  );
}
