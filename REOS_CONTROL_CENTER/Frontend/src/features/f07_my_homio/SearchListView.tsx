import SearchResultCard, {
  type SearchResultCardData,
} from "./SearchResultCard";

import styles from "./SearchListView.module.css";

type SearchListViewProps = Readonly<{
  properties: SearchResultCardData[];
  onSave?: (property: SearchResultCardData) => void;
  onCompare?: (property: SearchResultCardData) => void;
  savedIds?: string[];
  comparedIds?: string[];
}>;

export default function SearchListView({
  properties,
  onSave,
  onCompare,
  savedIds = [],
  comparedIds = [],
}: SearchListViewProps) {
  if (properties.length === 0) {
    return null;
  }

  return (
    <div className={styles.grid} aria-label="Property results">
      {properties.map((property) => {
        const identity = `${property.entityType}:${property.id}`;

        return (
          <SearchResultCard
            key={identity}
            property={property}
            onSave={onSave}
            onCompare={onCompare}
            saved={savedIds.includes(identity)}
            compared={comparedIds.includes(identity)}
          />
        );
      })}
    </div>
  );
}
