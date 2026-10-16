export type SearchSuggestionKind =
  | "location"
  | "project"
  | "property"
  | "recent"
  | "popular";

export type SearchSuggestion = Readonly<{
  id: string;
  kind: SearchSuggestionKind;
  title: string;
  description?: string;
  href: string;
}>;

export type ActiveSearchFilter = Readonly<{
  id: string;
  label: string;
  value: string;
}>;

export type SearchFilterSummaryData = Readonly<{
  resultCount?: number;
  resultCountLabel?: string;
  activeFilters: readonly ActiveSearchFilter[];
}>;
