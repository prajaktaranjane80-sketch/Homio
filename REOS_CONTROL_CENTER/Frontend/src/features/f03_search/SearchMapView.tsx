import type { SearchResultCardData } from "./SearchResultCard";
import styles from "./SearchMapView.module.css";

type SearchMapViewProps = Readonly<{
  properties: SearchResultCardData[];
  selectedId?: string;
  onSelect?: (property: SearchResultCardData) => void;
}>;

export default function SearchMapView({
  properties,
  selectedId,
  onSelect,
}: SearchMapViewProps) {
  return (
    <section
      className={styles.mapLayout}
      aria-label="Location preview and current search results"
    >
      <div className={styles.mapSurface}>
        <div className={styles.mapHeader}>
          <span>LOCATION PREVIEW</span>
          <small>Geographic map is not connected</small>
        </div>

        <div
          className={styles.mapCanvas}
          role="status"
          aria-live="polite"
        >
          <div className={styles.empty}>
            <strong>Live map unavailable</strong>
            <span>
              These preview records do not provide authoritative
              coordinates. HOMIO will not place estimated markers or
              present a decorative grid as a real map.
            </span>
          </div>
        </div>
      </div>

      <aside className={styles.sidePanel} aria-label="Current results">
        <div className={styles.sideHeader}>
          <strong>
            {properties.length.toLocaleString()} results on this page
          </strong>
          <span>Choose a result to highlight it in the list.</span>
        </div>

        <div className={styles.items}>
          {properties.map((property) => (
            <button
              key={property.id}
              type="button"
              className={`${styles.item} ${
                selectedId === property.id ? styles.itemSelected : ""
              }`}
              onClick={() => onSelect?.(property)}
              aria-pressed={selectedId === property.id}
            >
              <span className={styles.itemTitle}>
                {property.title}
              </span>

              <span>{property.location}</span>

              <strong>{property.price}</strong>
            </button>
          ))}
        </div>
      </aside>
    </section>
  );
}
