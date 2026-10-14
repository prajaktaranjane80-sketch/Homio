import type { SearchIntent } from "@/features/f03_search/search.types";

export type MyHomioSection =
  | "dashboard"
  | "profile"
  | "saved"
  | "compare"
  | "recent-searches"
  | "recent-views"
  | "enquiries"
  | "conversations"
  | "visits"
  | "recommendations"
  | "brokerage-journey"
  | "documents"
  | "notifications"
  | "settings";

export type MyHomioNavigationGroup =
  | "overview"
  | "discovery"
  | "journey"
  | "account";

export type MyHomioNavigationItem = Readonly<{
  id: MyHomioSection;
  label: string;
  group: MyHomioNavigationGroup;
  description: string;
}>;

export type MyHomioProfile = Readonly<{
  name?: string;
  email?: string;
  emailVerified: boolean;
}>;

export type MyHomioSearchIntent = SearchIntent;

export type MyHomioSearchDraft = Readonly<{
  href: string;
  intent: MyHomioSearchIntent;
  title: string;
  location?: string;
  filtersLabel?: string;
}>;

export type MyHomioRecentSearch = MyHomioSearchDraft &
  Readonly<{
    id: string;
    searchedAt: string;
  }>;

export type MyHomioSavedSearch = MyHomioSearchDraft &
  Readonly<{
    id: string;
    savedAt: string;
  }>;

export type MyHomioRecentView = Readonly<{
  id: string;
  kind: "property" | "project";
  title: string;
  href: string;
  subtitle?: string;
  viewedAt: string;
}>;

export type MyHomioActivitySnapshot = Readonly<{
  recentSearches: readonly MyHomioRecentSearch[];
  savedSearches: readonly MyHomioSavedSearch[];
  recentViews: readonly MyHomioRecentView[];
}>;
