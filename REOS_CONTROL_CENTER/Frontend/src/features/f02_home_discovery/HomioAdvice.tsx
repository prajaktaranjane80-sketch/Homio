import Link from "next/link";
import styles from "./HomioAdvice.module.css";

const articles = [
  {
    category: "BUYING",
    title: "How to evaluate a property before you enquire",
    description:
      "A practical framework for comparing location, property facts, project context and next-step readiness.",
    readTime: "6 min read",
    href: "/advice/evaluate-property-before-enquiry",
    image:
      "https://images.unsplash.com/photo-1560518883-ce09059eeffa?auto=format&fit=crop&w=1400&q=85",
  },
  {
    category: "INVESTMENT",
    title: "What makes a location attractive for property investment?",
    description:
      "Understand the signals that matter when comparing growth, rental demand, infrastructure and positioning.",
    readTime: "8 min read",
    href: "/advice/property-investment-location",
    image:
      "https://images.unsplash.com/photo-1444723121867-7a241cacace9?auto=format&fit=crop&w=1400&q=85",
  },
  {
    category: "RELOCATION",
    title: "Moving to a new city: the property questions to ask first",
    description:
      "Use a simple location-first checklist to narrow down the right neighbourhood and home type.",
    readTime: "5 min read",
    href: "/advice/relocation-property-checklist",
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
              Useful guides, market explainers and practical property knowledge
              designed to help you understand the decision before you enter the
              brokerage journey.
            </p>
          </div>

          <Link href="/advice" className={styles.viewAll}>
            Explore all advice
            <span aria-hidden="true">↗</span>
          </Link>
        </div>

        <div className={styles.topicBar} aria-label="Advice topics">
          {topics.map((topic) => (
            <Link key={topic} href={`/advice?topic=${topic.toLowerCase()}`}>
              {topic}
            </Link>
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
              <Link href={article.href} className={styles.imageLink}>
                <div className={styles.imageWrap}>
                  <img
                    src={article.image}
                    alt=""
                    className={styles.image}
                    loading="lazy"
                  />
                </div>
              </Link>

              <div className={styles.body}>
                <div className={styles.meta}>
                  <span>{article.category}</span>
                  <span>{article.readTime}</span>
                </div>

                <Link href={article.href} className={styles.title}>
                  {article.title}
                </Link>

                <p>{article.description}</p>

                <Link href={article.href} className={styles.read}>
                  Read guide
                  <span aria-hidden="true">→</span>
                </Link>
              </div>
            </article>
          ))}
        </div>

        <div className={styles.bottom}>
          <div>
            <span className={styles.bottomEyebrow}>KNOWLEDGE BEFORE ACTION</span>
            <strong>
              Learn, compare and understand the market before you take the next
              step.
            </strong>
          </div>

          <Link href="/advice" className={styles.bottomAction}>
            Visit HOMIO Advice
          </Link>
        </div>
      </div>
    </section>
  );
}
