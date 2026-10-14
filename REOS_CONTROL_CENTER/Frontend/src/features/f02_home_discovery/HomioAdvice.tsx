import Image from "next/image";
import styles from "./HomioAdvice.module.css";

const articles = [
  {
    category: "BUYING",
    title: "How to evaluate a property before you enquire",
    description:
      "A preview of how to compare location, property facts, project context and next-step readiness.",
    image:
      "https://images.unsplash.com/photo-1560518883-ce09059eeffa?auto=format&fit=crop&w=1400&q=85",
  },
  {
    category: "INVESTMENT",
    title: "What makes a location attractive for property investment?",
    description:
      "A guide concept covering growth signals, rental demand, infrastructure and positioning.",
    image:
      "https://images.unsplash.com/photo-1444723121867-7a241cacace9?auto=format&fit=crop&w=1400&q=85",
  },
  {
    category: "RELOCATION",
    title: "Moving to a new city: the property questions to ask first",
    description:
      "A preview of a location-first checklist for narrowing down a neighbourhood and home type.",
    image:
      "https://images.unsplash.com/photo-1494522358652-f30e61a60313?auto=format&fit=crop&w=1400&q=85",
  },
];

const topics = [
  "Buying",
  "Renting",
  "Investment",
  "Markets",
  "Projects",
  "Relocation",
];

export default function HomioAdvice() {
  return (
    <section id="advice" className={styles.section}>
      <div className="homio-container">
        <div className={styles.header}>
          <div>
            <span className={styles.eyebrow}>HOMIO ADVICE</span>

            <h2>Better property decisions start with better context.</h2>

            <p>
              These cards preview future guide content. They are not published
              articles, and the linked article-reading experience is not
              connected yet.
            </p>
          </div>

          <span className={styles.viewAll} aria-disabled="true">
            Advice experience preview
          </span>
        </div>

        <div className={styles.topicBar} aria-label="Advice topic previews">
          {topics.map((topic) => (
            <span key={topic} className={styles.viewAll}>
              {topic}
            </span>
          ))}
        </div>

        <div className={styles.grid}>
          {articles.map((article, index) => (
            <article
                  key={article.title}
                  className={`${styles.card} ${
                    index === 0 ? styles.featured : ""
                  }`}
                >
              <div className={styles.imageLink}>
                <div className={styles.imageWrap}>
                  
                  <Image
                    src={article.image}
                    width={1400}
                    height={900}
                    sizes="(max-width: 640px) 100vw, (max-width: 1000px) 50vw, 40vw"
                    alt=""
                    className={styles.image}
                    loading="lazy"
                  />

                </div>
              </div>

              <div className={styles.body}>
                <div className={styles.meta}>
                  <span>{article.category}</span>
                  <span>Guide preview</span>
                </div>

                <span className={styles.title}>{article.title}</span>
                <p>{article.description}</p>

                <span className={styles.read}>
                  Article workflow not active
                </span>
              </div>
            </article>
          ))}
        </div>

        <div className={styles.bottom}>
          <div>
            <span className={styles.bottomEyebrow}>
              KNOWLEDGE BEFORE ACTION
            </span>

            <strong>
              Learn, compare and understand the market before you take the next
              step.
            </strong>
          </div>

          <span className={styles.bottomAction} aria-disabled="true">
            Guides are preview-only
          </span>
        </div>
      </div>
    </section>
  );
}
