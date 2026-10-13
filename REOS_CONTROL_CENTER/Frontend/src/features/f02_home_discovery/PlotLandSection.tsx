import Link from "next/link";
import styles from "./PlotLandSection.module.css";

const categories = [
  {
    title: "Residential Plots",
    description:
      "Preview the land-search journey for residential plots. Live plot inventory is not connected yet.",
    href: "/search?intent=land&propertyType=Plot",
    image:
      "https://images.unsplash.com/photo-1500382017468-9049fed747ef?auto=format&fit=crop&w=1400&q=85",
  },
  {
    title: "Investment Land",
    description:
      "Preview land discovery with investment-related search context. No live investment-land feed is connected.",
    href: "/search?intent=land&propertyType=Land&q=investment",
    image:
      "https://images.unsplash.com/photo-1500534623283-312aade485b7?auto=format&fit=crop&w=1400&q=85",
  },
  {
    title: "Development Sites",
    description:
      "Preview search criteria for larger development parcels. Availability and permitted usage are not verified.",
    href: "/search?intent=land&propertyType=Land&q=development",
    image:
      "https://images.unsplash.com/photo-1494526585095-c41746248156?auto=format&fit=crop&w=1400&q=85",
  },
];

const facts = [
  "Location-first discovery",
  "Plot size and land context",
  "Development and usage context",
  "Brokerage next-step design",
];

export default function PlotLandSection() {
  return (
    <section className={styles.section} aria-labelledby="plot-land-heading">
      <div className="homio-container">
        <div className={styles.layout}>
          <div className={styles.intro}>
            <span className={styles.eyebrow}>PLOTS & LAND</span>

            <h2 id="plot-land-heading">
              Find the land behind
              <br />
              the next opportunity.
            </h2>

            <p>
              Explore land-search criteria through the HOMIO experience.
              The current F03 preview dataset contains buy-property examples
              only; active plot and land inventory is not connected yet.
            </p>

            <Link
              href="/search?intent=land"
              className={styles.primaryAction}
            >
              Open land-search preview
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
                  
                  <Image
                    src={category.image}
                    width={1400}
                    height={900}
                    sizes="(max-width: 650px) 100vw, (max-width: 900px) 50vw, 33vw"
                    alt={`Illustrative image for ${category.title}`}
                    className={styles.image}
                    loading="lazy"
                  />

                </div>

                <div className={styles.cardBody}>
                  <h3>{category.title}</h3>
                  <p>{category.description}</p>

                  <span className={styles.cardLink}>
                    Open search preview
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
              Start with location. Understand the criteria. Verify availability
              before taking action.
            </strong>
          </div>

          <Link
            href="/search?intent=land"
            className={styles.bottomAction}
          >
            Open land search
          </Link>
        </div>
      </div>
    </section>
  );
}
