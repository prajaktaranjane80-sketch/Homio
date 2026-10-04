import Link from "next/link";
import styles from "./SaveCompareSection.module.css";

const savedItems = [
  {
    type: "PROPERTY",
    title: "Marina Crest Residence",
    location: "Dubai Marina",
    price: "AED 2.10M",
    image:
      "https://images.unsplash.com/photo-1600607688969-a5bfcd646154?auto=format&fit=crop&w=1000&q=85",
  },
  {
    type: "PROJECT",
    title: "Harbour Residences",
    location: "Dubai Harbour",
    price: "From AED 2.40M",
    image:
      "https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?auto=format&fit=crop&w=1000&q=85",
  },
  {
    type: "PROPERTY",
    title: "Central Garden Residence",
    location: "Singapore",
    price: "SGD 2.85M",
    image:
      "https://images.unsplash.com/photo-1600210492486-724fe5c67fb0?auto=format&fit=crop&w=1000&q=85",
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
              Save the properties and projects that matter, compare them side
              by side, and return to your journey when you are ready.
            </p>
          </div>

          <Link href="/saved" className={styles.viewAll}>
            Open saved
            <span aria-hidden="true">↗</span>
          </Link>
        </div>

        <div className={styles.layout}>
          <div className={styles.savedPanel}>
            <div className={styles.panelHeader}>
              <div>
                <span className={styles.panelLabel}>YOUR SHORTLIST</span>
                <h3>Recently saved</h3>
              </div>

              <span className={styles.count}>3 items</span>
            </div>

            <div className={styles.savedList}>
              {savedItems.map((item) => (
                <article key={item.title} className={styles.savedItem}>
                  <div className={styles.itemImageWrap}>
                    <img
                      src={item.image}
                      alt={item.title}
                      className={styles.itemImage}
                      loading="lazy"
                    />
                  </div>

                  <div className={styles.itemBody}>
                    <span className={styles.itemType}>{item.type}</span>

                    <Link href="/saved" className={styles.itemTitle}>
                      {item.title}
                    </Link>

                    <p>{item.location}</p>

                    <strong>{item.price}</strong>
                  </div>

                  <Link
                    href="/saved"
                    className={styles.itemArrow}
                    aria-label={`Open saved item ${item.title}`}
                  >
                    ↗
                  </Link>
                </article>
              ))}
            </div>

            <Link href="/saved" className={styles.panelAction}>
              View all saved items
              <span aria-hidden="true">→</span>
            </Link>
          </div>

          <div className={styles.comparePanel}>
            <div className={styles.compareVisual}>
              <div className={styles.compareHeader}>
                <span className={styles.panelLabel}>COMPARE</span>

                <span className={styles.compareCount}>3 selected</span>
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
                    <strong>Compare</strong>
                  </div>
                ))}
              </div>
            </div>

            <div className={styles.compareBody}>
              <h3>Compare before you decide.</h3>

              <p>
                Move beyond individual listings and see the differences across
                the properties you are actually considering.
              </p>

              <Link href="/compare" className={styles.compareAction}>
                Start comparing
                <span aria-hidden="true">→</span>
              </Link>
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

          <Link href="/my" className={styles.bottomAction}>
            Open My HOMIO
          </Link>
        </div>
      </div>
    </section>
  );
}
