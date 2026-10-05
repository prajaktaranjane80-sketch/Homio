"use client";

import SearchListView from "./SearchListView";
import SearchMapView from "./SearchMapView";
import type { SearchResultCardData } from "./SearchResultCard";
import type { SearchViewMode } from "./search.types";
import styles from "./SearchResults.module.css";

type SearchResultsProps = Readonly<{
  properties: SearchResultCardData[];
  viewMode: SearchViewMode;
  savedIds: string[];
  comparedIds: string[];
  selectedId?: string;
  onSave: (property: SearchResultCardData) => void;
  onCompare: (property: SearchResultCardData) => void;
  onSelect: (property: SearchResultCardData) => void;
}>;

export default function SearchResults({
  properties,
  viewMode,
  savedIds,
  comparedIds,
  selectedId,
  onSave,
  onCompare,
  onSelect,
}: SearchResultsProps) {
  return (
    <section className={styles.section} aria-label="Search results">
      {viewMode === "map" ? (
        <SearchMapView
          properties={properties}
          selectedId={selectedId}
          onSelect={onSelect}
        />
      ) : (
        <SearchListView
          properties={properties}
          onSave={onSave}
          onCompare={onCompare}
          savedIds={savedIds}
          comparedIds={comparedIds}
        />
      )}
    </section>
  );
}
