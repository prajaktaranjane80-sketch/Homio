import Link from "next/link";
import styles from "./HomioAISection.module.css";

const suggestions = [
  "Kalyani Nagar",
  "Baner",
  "Investment Home",
  "Contemporary 3 BHK Residence",
];

const contextItems = [
  "Search intent preview",
  "Location context preview",
  "Saved-items concept",
  "Market context preview",
];

export default function HomioAISection() {
  return (
    <section id="homio-ai" className={styles.section}>
      <div className="homio-container">
        <div className={styles.shell}>
          <div className={styles.content}>
            <span className={styles.eyebrow}>HOMIO AI · EXPERIENCE PREVIEW</span>

            <h2>
              Search less.
              <br />
              Understand more.
            </h2>

            <p>
              This panel demonstrates the planned HOMIO AI interface. A live
              AI session, saved-account context and market-intelligence
              integration are not connected here. You can use the standard
              property search below.
            </p>

            <div className={styles.actions}>
              <span className={styles.primary} aria-disabled="true">
                AI interaction preview only
              </span>

              <Link href="/search" className={styles.secondary}>
                Continue normal search
              </Link>
            </div>

            <div className={styles.suggestions}>
              <span className={styles.suggestionLabel}>
                TRY A STANDARD PROPERTY SEARCH
              </span>

              <div className={styles.chips}>
                {suggestions.map((suggestion) => (
                  <Link
                    key={suggestion}
                    href={`/search?q=${encodeURIComponent(suggestion)}`}
                  >
                    {suggestion}
                  </Link>
                ))}
              </div>
            </div>
          </div>

          <div className={styles.aiPanel}>
            <div className={styles.panelHeader}>
              <div className={styles.aiMark} aria-hidden="true">
                H
              </div>

              <div>
                <strong>HOMIO AI</strong>
                <span>Interface experience preview</span>
              </div>

              <span
                className={styles.live}
                aria-label="AI conversation is a preview, not an active service"
              >
                Preview only
              </span>
            </div>

            <div className={styles.messages}>
              <div className={`${styles.message} ${styles.userMessage}`}>
                I want a premium 2-bedroom home close to the city.
              </div>

              <div className={`${styles.message} ${styles.aiMessage}`}>
                Illustrative response: narrow the location, property type and
                budget first. This is example copy, not a live AI response.
              </div>

              <div className={styles.contextBox}>
                <span>Example context elements — not connected data</span>

                <div className={styles.contextGrid}>
                  {contextItems.map((item) => (
                    <div key={item}>
                      <span className={styles.contextCheck} aria-hidden="true">
                        ◇
                      </span>
                      {item}
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className={styles.input}>
              <span>Live AI input is not enabled in this preview.</span>

              <button
                type="button"
                aria-label="AI conversation is not active"
                title="AI conversation is not active in this preview"
                disabled
              >
                →
              </button>
            </div>
          </div>
        </div>

        <div className={styles.bottom}>
          <span>
            <strong>AI supports the journey.</strong> HOMIO brokerage remains
            the intended action layer when the relevant workflows are connected.
          </span>

          <Link href="/search">Explore property search</Link>
        </div>
      </div>
    </section>
  );
}
