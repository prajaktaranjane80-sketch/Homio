import type {
  SearchCurrency,
  SearchIntent,
  SearchSort,
  SearchViewMode,
} from "./search.types";

export const SEARCH_INTENTS: SearchIntent[] = [
  "buy",
  "rent",
  "commercial",
  "projects",
  "land",
];

export const SEARCH_INTENT_LABELS: Record<SearchIntent, string> = {
  buy: "Buy",
  rent: "Rent",
  commercial: "Commercial",
  projects: "Projects",
  land: "Land",
};

export const SEARCH_PROPERTY_TYPES = [
  "Apartment",
  "Villa",
  "Independent House",
  "Plot",
  "Office",
  "Retail",
  "Warehouse",
  "Land",
] as const;

export const SEARCH_PROPERTY_STATUSES = [
  "Ready to move",
  "Under construction",
  "New launch",
  "Resale",
  "Pre-launch",
] as const;

export const SEARCH_FURNISHING_OPTIONS = [
  "Unfurnished",
  "Semi-furnished",
  "Fully furnished",
] as const;

export const SEARCH_POSSESSION_OPTIONS = [
  "Ready now",
  "Within 3 months",
  "Within 6 months",
  "Within 12 months",
  "After 12 months",
] as const;

export const SEARCH_AMENITIES = [
  "Parking",
  "Swimming Pool",
  "Gym",
  "Security",
  "Lift",
  "Garden",
  "Balcony",
  "Clubhouse",
  "Power Backup",
  "Pet Friendly",
  "Concierge",
  "CCTV",
] as const;

export const SEARCH_CURRENCIES: ReadonlyArray<{
  value: SearchCurrency;
  label: string;
  symbol: string;
}> = [
  { value: "INR", label: "INR — Indian rupee", symbol: "₹" },
  { value: "AED", label: "AED — UAE dirham", symbol: "AED" },
  { value: "SGD", label: "SGD — Singapore dollar", symbol: "SGD" },
  { value: "JPY", label: "JPY — Japanese yen", symbol: "¥" },
];

export const SEARCH_SORT_OPTIONS: Array<{
  value: SearchSort;
  label: string;
}> = [
  { value: "relevance", label: "Relevance" },
  { value: "newest", label: "Newest" },
  {
    value: "price_low_to_high",
    label: "Price: low to high (selected currency)",
  },
  {
    value: "price_high_to_low",
    label: "Price: high to low (selected currency)",
  },
  {
    value: "area_high_to_low",
    label: "Area: largest first",
  },
];

export const SEARCH_VIEW_MODES: SearchViewMode[] = ["list", "map"];

/** Results per page in the current experience preview. */
export const SEARCH_DEFAULT_PAGE_SIZE = 12;
export const SEARCH_MAX_PAGE_SIZE = 48;

export const SEARCH_DEFAULTS = {
  intent: "buy" as SearchIntent,
  sort: "relevance" as SearchSort,
  viewMode: "list" as SearchViewMode,
  page: 1,
  pageSize: SEARCH_DEFAULT_PAGE_SIZE,
};

export const SEARCH_QUERY_KEYS = {
  intent: "intent",
  query: "q",
  country: "country",
  city: "city",
  district: "district",
  locality: "locality",
  landmark: "landmark",

  /** Geographic/project context. */
  project: "project",

  /** Independent advanced filters; do not reuse the location key. */
  filterProject: "projectName",
  builder: "builder",

  propertyType: "propertyType",
  minBudget: "minBudget",
  maxBudget: "maxBudget",
  budgetCurrency: "budgetCurrency",
  bedrooms: "bedrooms",
  minArea: "minArea",
  maxArea: "maxArea",
  status: "status",
  furnishing: "furnishing",
  amenities: "amenities",
  possession: "possession",
  verified: "verified",
  sort: "sort",
  view: "view",
  page: "page",
} as const;
