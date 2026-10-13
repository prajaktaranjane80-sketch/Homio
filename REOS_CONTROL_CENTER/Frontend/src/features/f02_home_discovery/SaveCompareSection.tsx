import Link from "next/link";
import styles from "./SaveCompareSection.module.css";

const savedItems = [
  {
    type: "PROPERTY",
    title: "Skyline Residence",
    location: "Dubai Marina, Dubai",
    price: "AED 3.25M",
    image:
      "https://images.unsplash.com/photo-1600607688969-a5bfcd646154?auto=format&fit=crop&w=1000&q=85",
    href: "/property/skyline-residence",
  },
  {
    type: "PROJECT",
    title: "Harbour Residences",
    location: "Dubai Harbour",
    price: "Preview only",
    image:
      "https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?auto=format&fit=crop&w=1000&q=85",
    href: "/project/harbour-residences",
  },
  {
    type: "PROPERTY",
    title: "Central Park Residence",
    location: "Downtown Dubai",
    price: "AED 2.10M",
    image:
      "https://images.unsplash.com/photo-1600210492486-724fe5c67fb0?auto=format&fit=crop&w=1000&q=85",
    href: "/property/central-park-residence",
  },
];

const comparePoints = [
  "Price and size",
  "Property type",
  "Location context",
  "Project information",
  "Availability signals",
];

export default function SaveCompareSection() {
  return (
    <section id="save-compare" className={styles.section}>
      <div className="homio-container">
        <div className={styles.header}>
          <div>
            <span className={styles.eyebrow}>SAVE & COMPARE</span>

            <h2>Keep your shortlist together.</h2>

            <p>
              The items below are examples of the intended shortlist layout.
              They are not saved to a user account, and no comparison state is
              being persisted in this homepage preview.
            </p>
          </div>

          <span className={styles.viewAll} aria-disabled="true">
            Shortlist preview only
          </span>
        </div>

        <div className={styles.layout}>
          <div className={styles.savedPanel}>
            <div className={styles.panelHeader}>
              <div>
                <span className={styles.panelLabel}>EXAMPLE SHORTLIST</span>
                <h3>Illustrative items</h3>
              </div>

              <span className={styles.count}>3 examples</span>
            </div>

            <div className={styles.savedList}>
              {savedItems.map((item) => (
                <article key={item.title} className={styles.savedItem}>
                  <div className={styles.itemImageWrap}>
                    
                  <Image
                    src={item.image}
                    width={164}
                    height={144}
                    sizes="82px"
                    alt=""
                    className={styles.itemImage}
                    loading="lazy"
                  />

                  </div>

                  <div className={styles.itemBody}>
                    <span className={styles.itemType}>{item.type}</span>

                    <Link href={item.href} className={styles.itemTitle}>
                      {item.title}
                    </Link>

                    <p>{item.location}</p>
                    <strong>{item.price}</strong>
                  </div>

                  <Link
                    href={item.href}
                    className={styles.itemArrow}
                    aria-label={`Open ${item.title} experience preview`}
                  >
                    ↗
                  </Link>
                </article>
              ))}
            </div>

            <Link
              href="/search?intent=buy"
              className={styles.panelAction}
            >
              Browse property previews
              <span aria-hidden="true">→</span>
            </Link>
          </div>

          <div className={styles.comparePanel}>
            <div className={styles.compareVisual}>
              <div className={styles.compareHeader}>
                <span className={styles.panelLabel}>COMPARISON PREVIEW</span>
                <span className={styles.compareCount}>Example layout</span>
              </div>

              <div className={styles.compareCards}>
                {savedItems.map((item, index) => (
                  <div
                    key={`${item.title}-${index}`}
                    className={styles.compareCard}
                  >
                    <img
                      src={item.image}
                      alt=""
                      className={styles.compareImage}
                    />

                    <span>{index + 1}</span>
                  </div>
                ))}
              </div>

              <div className={styles.compareTable}>
                {comparePoints.map((point) => (
                  <div key={point} className={styles.compareRow}>
                    <span>{point}</span>
                    <strong>Preview</strong>
                  </div>
                ))}
              </div>
            </div>

            <div className={styles.compareBody}>
              <h3>Compare before you decide.</h3>

              <p>
                This visual demonstrates a possible comparison layout.
                Interactive selection, data comparison and saved comparison
                state are not active.
              </p>

              <span className={styles.compareAction} aria-disabled="true">
                Comparison workflow not active
              </span>
            </div>
          </div>
        </div>

        <div className={styles.bottom}>
          <div>
            <span className={styles.bottomLabel}>YOUR JOURNEY</span>

            <strong>
              Save now. Compare later. Continue where you left off.
            </strong>
          </div>

          <Link href="/#my-homio" className={styles.bottomAction}>
            Explore My HOMIO preview
          </Link>
        </div>
      </div>
    </section>
  );
}
