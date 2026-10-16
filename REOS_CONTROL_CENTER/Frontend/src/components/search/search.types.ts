
export type SearchSuggestionKind = "location" | "project" | "property";

export type SearchSuggestion = Readonly<{
  id: string;
  kind: SearchSuggestionKind;
  label: string;
  value: string;
  description?: string;
  meta?: string;
}>;

export type SearchActiveFilter = Readonly<{
  id: string;
  label: string;
}>;

export type SearchRecentItemData = Readonly<{
  id: string;
  query: string;
}>;

export type SearchPopularItemData = Readonly<{
  id: string;
  query: string;
}>;
