export type SearchIntent =
  | "buy"
  | "rent"
  | "commercial"
  | "projects"
  | "land";

export type SearchViewMode = "list" | "map";

export type SearchSort =
  | "relevance"
  | "newest"
  | "price_low_to_high"
  | "price_high_to_low"
  | "area_high_to_low";

export type SearchLocation = {
  country?: string;
  city?: string;
  district?: string;
  locality?: string;
  landmark?: string;
  project?: string;
  label: string;
};

export type SearchFilters = {
  propertyTypes: string[];
  budgetMin?: number;
  budgetMax?: number;
  bedrooms: number[];
  areaMin?: number;
  areaMax?: number;
  propertyStatus: string[];
  furnishing: string[];
  amenities: string[];
  project?: string;
  builder?: string;
  possession?: string[];
  verifiedOnly?: boolean;
};

export type SearchState = {
  intent: SearchIntent;
  location?: SearchLocation;
  filters: SearchFilters;
  sort: SearchSort;
  viewMode: SearchViewMode;
  page: number;
  query?: string;
};

export type SearchSummary = {
  totalResults: number;
  activeFilters: number;
  locationLabel?: string;
  intent: SearchIntent;
};
