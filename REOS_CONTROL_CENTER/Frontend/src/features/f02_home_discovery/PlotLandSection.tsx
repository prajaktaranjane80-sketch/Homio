import Link from "next/link";
import styles from "./PlotLandSection.module.css";

const categories = [
  {
    title: "Residential Plots",
    description:
      "Land opportunities for villas, custom homes and future residential projects.",
    href: "/search?intent=land&type=residential-plot",
    image:
      "https://images.unsplash.com/photo-1500382017468-9049fed747ef?auto=format&fit=crop&w=1400&q=85",
  },
  {
    title: "Investment Land",
    description:
      "Explore land opportunities around developing locations and long-term potential.",
    href: "/search?intent=land&type=investment",
    image:
      "https://images.unsplash.com/photo-1500534623283-312aade485b7?auto=format&fit=crop&w=1400&q=85",
  },
  {
    title: "Development Sites",
    description:
      "Larger land parcels suited to development and commercial opportunities.",
    href: "/search?intent=land&type=development",
    image:
      "https://images.unsplash.com/photo-1494526585095-c41746248156?auto=format&fit=crop&w=1400&q=85",
  },
];

const facts = [
  "Location-first discovery",
  "Plot size and land context",
  "Development and usage context",
  "Direct HOMIO enquiry journey",
];

export default function PlotLandSection() {
  return (
    <section className={styles.section}>
      <div className="homio-container">
        <div className={styles.layout}>
          <div className={styles.intro}>
            <span className={styles.eyebrow}>PLOTS & LAND</span>

            <h2>
              Find the land behind
              <br />
              the next opportunity.
            </h2>

            <p>
              Discover residential plots, investment land and development
              opportunities with location, size and market context presented
              before your enquiry.
            </p>

            <Link
              href="/search?intent=land"
              className={styles.primaryAction}
            >
              Explore plots & land
              <span aria-hidden="true">↗</span>
            </Link>

            <div className={styles.facts}>
              {facts.map((fact) => (
                <div key={fact} className={styles.fact}>
                  <span className={styles.factIcon} aria-hidden="true">
                    ✓
                  </span>
                  <span>{fact}</span>
                </div>
              ))}
            </div>
          </div>

          <div className={styles.cards}>
            {categories.map((category) => (
              <Link
                key={category.title}
                href={category.href}
                className={styles.card}
              >
                <div className={styles.imageWrap}>
                  <img
                    src={category.image}
                    alt={category.title}
                    className={styles.image}
                    loading="lazy"
                  />
                </div>

                <div className={styles.cardBody}>
                  <h3>{category.title}</h3>

                  <p>{category.description}</p>

                  <span className={styles.cardLink}>
                    Explore
                    <span aria-hidden="true">→</span>
                  </span>
                </div>
              </Link>
            ))}
          </div>
        </div>

        <div className={styles.bottom}>
          <div>
            <span className={styles.bottomLabel}>LAND DISCOVERY</span>
            <strong>
              Start with the location. Understand the opportunity. Then
              connect with HOMIO.
            </strong>
          </div>

          <Link
            href="/search?intent=land"
            className={styles.bottomAction}
          >
            Start land search
          </Link>
        </div>
      </div>
    </section>
  );
}
