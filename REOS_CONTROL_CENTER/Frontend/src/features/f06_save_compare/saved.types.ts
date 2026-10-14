export type SavedEntityKind = "property" | "project" | "locality";

/** Presentation record mapped from a verified source; not a business aggregate. */
export type SavedRecord = Readonly<{
  id: string;
  kind: SavedEntityKind;
  title: string;
  href?: string;
  subtitle?: string;
  imageUrl?: string;
  statusLabel?: string;
  detailLine?: string;
  savedAt?: string;
}>;

/** A saved query/context. Its filter summary must come from the approved search adapter. */
export type SavedSearchRecord = Readonly<{
  id: string;
  title: string;
  href?: string;
  filtersSummary?: string;
  updatedAt?: string;
}>;

/** A navigation-history entry, not an authoritative interaction or transaction record. */
export type RecentViewRecord = Readonly<{
  id: string;
  kind: SavedEntityKind;
  title: string;
  href?: string;
  subtitle?: string;
  viewedAt?: string;
}>;

export type SavedTab =
  | "properties"
  | "projects"
  | "localities"
  | "searches"
  | "recent";

export type PersistenceStatus = "connected" | "session-only" | "not-connected";
