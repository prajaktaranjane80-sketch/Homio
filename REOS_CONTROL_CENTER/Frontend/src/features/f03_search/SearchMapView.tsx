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
    <section className={styles.mapLayout} aria-label="Map property results">
      <div className={styles.mapSurface}>
        <div className={styles.mapHeader}>
          <span>HOMIO MAP VIEW</span>
          <small>Location-based discovery</small>
        </div>

        <div className={styles.mapCanvas}>
          <div className={styles.gridPattern} aria-hidden="true" />

          {properties.slice(0, 12).map((property, index) => (
            <button
              key={property.id}
              type="button"
              className={`${styles.marker} ${
                selectedId === property.id ? styles.selected : ""
              }`}
              style={{
                left: `${15 + ((index * 17) % 72)}%`,
                top: `${18 + ((index * 29) % 62)}%`,
              }}
              onClick={() => onSelect?.(property)}
              aria-label={`View ${property.title}`}
            >
              <span>{property.price}</span>
            </button>
          ))}

          {properties.length === 0 ? (
            <div className={styles.empty}>
              <strong>No mapped properties yet</strong>
              <span>Broader map coverage will appear as inventory is added.</span>
            </div>
          ) : null}
        </div>
      </div>

      <aside className={styles.sidePanel} aria-label="Map result list">
        <div className={styles.sideHeader}>
          <strong>{properties.length.toLocaleString()} properties</strong>
          <span>Map selection</span>
        </div>

        <div className={styles.items}>
          {properties.slice(0, 8).map((property) => (
            <button
              key={property.id}
              type="button"
              className={`${styles.item} ${
                selectedId === property.id ? styles.itemSelected : ""
              }`}
              onClick={() => onSelect?.(property)}
            >
              <span className={styles.itemTitle}>{property.title}</span>
              <span>{property.location}</span>
              <strong>{property.price}</strong>
            </button>
          ))}
        </div>
      </aside>
    </section>
  );
}
