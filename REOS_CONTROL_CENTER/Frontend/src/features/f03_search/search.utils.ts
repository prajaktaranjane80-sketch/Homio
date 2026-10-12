import {
  SEARCH_DEFAULTS,
  SEARCH_QUERY_KEYS,
} from "./search.constants";

import type {
  SearchCurrency,
  SearchFilters,
  SearchIntent,
  SearchSort,
  SearchState,
  SearchViewMode,
} from "./search.types";

const VALID_CURRENCIES: readonly SearchCurrency[] = [
  "INR",
  "AED",
  "SGD",
  "JPY",
];

export function countActiveFilters(filters: SearchFilters): number {
  let count = 0;

  count += filters.propertyTypes.length;
  count += filters.bedrooms.length;
  count += filters.propertyStatus.length;
  count += filters.furnishing.length;
  count += filters.amenities.length;
  count += filters.possession.length;

  if (filters.budgetMin !== undefined) count += 1;
  if (filters.budgetMax !== undefined) count += 1;
  if (filters.areaMin !== undefined) count += 1;
  if (filters.areaMax !== undefined) count += 1;
  if (filters.project?.trim()) count += 1;
  if (filters.builder?.trim()) count += 1;
  if (filters.verifiedOnly) count += 1;

  return count;
}

export function createEmptySearchFilters(): SearchFilters {
  return {
    propertyTypes: [],
    bedrooms: [],
    budgetCurrency: "INR",
    propertyStatus: [],
    furnishing: [],
    amenities: [],
    possession: [],
    verifiedOnly: false,
  };
}

export function createDefaultSearchState(): SearchState {
  return {
    intent: SEARCH_DEFAULTS.intent,
    filters: createEmptySearchFilters(),
    sort: SEARCH_DEFAULTS.sort,
    viewMode: SEARCH_DEFAULTS.viewMode,
    page: SEARCH_DEFAULTS.page,
  };
}

function cleanOptionalString(
  value: string | null,
): string | undefined {
  const normalized = value?.trim();
  return normalized ? normalized : undefined;
}

function parseNumber(value: string | null): number | undefined {
  if (!value || value.trim() === "") {
    return undefined;
  }

  const parsed = Number(value);

  if (
    !Number.isFinite(parsed) ||
    parsed < 0 ||
    parsed > 1_000_000_000_000_000
  ) {
    return undefined;
  }

  return parsed;
}

function parseList(value: string | null): string[] {
  if (!value) {
    return [];
  }

  return [
    ...new Set(
      value
        .split(",")
        .map((item) => item.trim())
        .filter(Boolean),
    ),
  ].slice(0, 40);
}

function parseBedrooms(value: string | null): number[] {
  return [
    ...new Set(
      parseList(value)
        .map(Number)
        .filter(
          (item) =>
            Number.isInteger(item) &&
            item >= 1 &&
            item <= 20,
        ),
    ),
  ];
}

function parseCurrency(value: string | null): SearchCurrency {
  if (
    value &&
    VALID_CURRENCIES.includes(value as SearchCurrency)
  ) {
    return value as SearchCurrency;
  }

  return "INR";
}

function parseIntent(value: string | null): SearchIntent {
  if (
    value === "buy" ||
    value === "rent" ||
    value === "commercial" ||
    value === "projects" ||
    value === "land"
  ) {
    return value;
  }

  return SEARCH_DEFAULTS.intent;
}

function parseSort(value: string | null): SearchSort {
  if (
    value === "relevance" ||
    value === "newest" ||
    value === "price_low_to_high" ||
    value === "price_high_to_low" ||
    value === "area_high_to_low"
  ) {
    return value;
  }

  return SEARCH_DEFAULTS.sort;
}

function parseView(value: string | null): SearchViewMode {
  return value === "map" ? "map" : SEARCH_DEFAULTS.viewMode;
}

function parsePositiveInteger(
  value: string | null,
  fallback: number,
): number {
  const parsed = Number(value);

  if (
    !Number.isInteger(parsed) ||
    parsed < 1 ||
    parsed > 10_000
  ) {
    return fallback;
  }

  return parsed;
}

function buildLocationFromParams(
  params: URLSearchParams,
): SearchState["location"] {
  const country = cleanOptionalString(
    params.get(SEARCH_QUERY_KEYS.country),
  );
  const city = cleanOptionalString(
    params.get(SEARCH_QUERY_KEYS.city),
  );
  const district = cleanOptionalString(
    params.get(SEARCH_QUERY_KEYS.district),
  );
  const locality = cleanOptionalString(
    params.get(SEARCH_QUERY_KEYS.locality),
  );
  const landmark = cleanOptionalString(
    params.get(SEARCH_QUERY_KEYS.landmark),
  );
  const project = cleanOptionalString(
    params.get(SEARCH_QUERY_KEYS.project),
  );

  const label =
    project ||
    locality ||
    landmark ||
    city ||
    district ||
    country;

  if (!label) {
    return undefined;
  }

  return {
    country,
    city,
    district,
    locality,
    landmark,
    project,
    label,
  };
}

export function searchStateFromParams(
  params: URLSearchParams,
): SearchState {
  return {
    intent: parseIntent(params.get(SEARCH_QUERY_KEYS.intent)),
    query: cleanOptionalString(
      params.get(SEARCH_QUERY_KEYS.query),
    ),
    location: buildLocationFromParams(params),
    filters: {
      propertyTypes: parseList(
        params.get(SEARCH_QUERY_KEYS.propertyType),
      ),
      budgetMin: parseNumber(
        params.get(SEARCH_QUERY_KEYS.minBudget),
      ),
      budgetMax: parseNumber(
        params.get(SEARCH_QUERY_KEYS.maxBudget),
      ),
      budgetCurrency: parseCurrency(
        params.get(SEARCH_QUERY_KEYS.budgetCurrency),
      ),
      bedrooms: parseBedrooms(
        params.get(SEARCH_QUERY_KEYS.bedrooms),
      ),
      areaMin: parseNumber(
        params.get(SEARCH_QUERY_KEYS.minArea),
      ),
      areaMax: parseNumber(
        params.get(SEARCH_QUERY_KEYS.maxArea),
      ),
      propertyStatus: parseList(
        params.get(SEARCH_QUERY_KEYS.status),
      ),
      furnishing: parseList(
        params.get(SEARCH_QUERY_KEYS.furnishing),
      ),
      amenities: parseList(
        params.get(SEARCH_QUERY_KEYS.amenities),
      ),
      project: cleanOptionalString(
        params.get(SEARCH_QUERY_KEYS.filterProject),
      ),
      builder: cleanOptionalString(
        params.get(SEARCH_QUERY_KEYS.builder),
      ),
      possession: parseList(
        params.get(SEARCH_QUERY_KEYS.possession),
      ),
      verifiedOnly:
        params.get(SEARCH_QUERY_KEYS.verified) === "true",
    },
    sort: parseSort(params.get(SEARCH_QUERY_KEYS.sort)),
    viewMode: parseView(params.get(SEARCH_QUERY_KEYS.view)),
    page: parsePositiveInteger(
      params.get(SEARCH_QUERY_KEYS.page),
      SEARCH_DEFAULTS.page,
    ),
  };
}

function writeList(
  params: URLSearchParams,
  key: string,
  values: Array<string | number>,
): void {
  if (values.length > 0) {
    params.set(key, values.join(","));
  }
}

/**
 * Serializes every supported search dimension into shareable URL parameters.
 * The new URL is built from scratch so stale filter keys cannot survive.
 */
export function searchStateToParams(
  state: SearchState,
): URLSearchParams {
  const params = new URLSearchParams();

  params.set(SEARCH_QUERY_KEYS.intent, state.intent);

  if (state.query?.trim()) {
    params.set(SEARCH_QUERY_KEYS.query, state.query.trim());
  }

  if (state.location?.country) {
    params.set(SEARCH_QUERY_KEYS.country, state.location.country);
  }

  if (state.location?.city) {
    params.set(SEARCH_QUERY_KEYS.city, state.location.city);
  }

  if (state.location?.district) {
    params.set(SEARCH_QUERY_KEYS.district, state.location.district);
  }

  if (state.location?.locality) {
    params.set(SEARCH_QUERY_KEYS.locality, state.location.locality);
  }

  if (state.location?.landmark) {
    params.set(SEARCH_QUERY_KEYS.landmark, state.location.landmark);
  }

  if (state.location?.project) {
    params.set(SEARCH_QUERY_KEYS.project, state.location.project);
  }

  writeList(
    params,
    SEARCH_QUERY_KEYS.propertyType,
    state.filters.propertyTypes,
  );

  writeList(
    params,
    SEARCH_QUERY_KEYS.bedrooms,
    state.filters.bedrooms,
  );

  writeList(
    params,
    SEARCH_QUERY_KEYS.status,
    state.filters.propertyStatus,
  );

  writeList(
    params,
    SEARCH_QUERY_KEYS.furnishing,
    state.filters.furnishing,
  );

  writeList(
    params,
    SEARCH_QUERY_KEYS.amenities,
    state.filters.amenities,
  );

  writeList(
    params,
    SEARCH_QUERY_KEYS.possession,
    state.filters.possession,
  );

  if (state.filters.project?.trim()) {
    params.set(
      SEARCH_QUERY_KEYS.filterProject,
      state.filters.project.trim(),
    );
  }

  if (state.filters.builder?.trim()) {
    params.set(
      SEARCH_QUERY_KEYS.builder,
      state.filters.builder.trim(),
    );
  }

  if (state.filters.budgetMin !== undefined) {
    params.set(
      SEARCH_QUERY_KEYS.minBudget,
      String(state.filters.budgetMin),
    );
  }

  if (state.filters.budgetMax !== undefined) {
    params.set(
      SEARCH_QUERY_KEYS.maxBudget,
      String(state.filters.budgetMax),
    );
  }

  const hasBudgetRange =
    state.filters.budgetMin !== undefined ||
    state.filters.budgetMax !== undefined;

  const priceSortSelected =
    state.sort === "price_low_to_high" ||
    state.sort === "price_high_to_low";

  if (hasBudgetRange || priceSortSelected) {
    params.set(
      SEARCH_QUERY_KEYS.budgetCurrency,
      state.filters.budgetCurrency,
    );
  }

  if (state.filters.areaMin !== undefined) {
    params.set(
      SEARCH_QUERY_KEYS.minArea,
      String(state.filters.areaMin),
    );
  }

  if (state.filters.areaMax !== undefined) {
    params.set(
      SEARCH_QUERY_KEYS.maxArea,
      String(state.filters.areaMax),
    );
  }

  if (state.filters.verifiedOnly) {
    params.set(SEARCH_QUERY_KEYS.verified, "true");
  }

  if (state.sort !== SEARCH_DEFAULTS.sort) {
    params.set(SEARCH_QUERY_KEYS.sort, state.sort);
  }

  if (state.viewMode !== SEARCH_DEFAULTS.viewMode) {
    params.set(SEARCH_QUERY_KEYS.view, state.viewMode);
  }

  if (state.page > SEARCH_DEFAULTS.page) {
    params.set(SEARCH_QUERY_KEYS.page, String(state.page));
  }

  return params;
}

export function normalizePageSize(value?: number): number {
  if (!value || !Number.isFinite(value) || value < 1) {
    return SEARCH_DEFAULTS.pageSize;
  }

  return Math.min(
    Math.floor(value),
    SEARCH_MAX_PAGE_SIZE,
  );
}

export function buildSearchQuery(state: SearchState): string {
  return searchStateToParams({
    ...state,
    page: state.page > 0 ? state.page : 1,
  }).toString();
}

export function hasSearchCriteria(state: SearchState): boolean {
  return Boolean(
    state.query?.trim() ||
      state.location ||
      countActiveFilters(state.filters) > 0,
  );
}

/**
 * "Clear filters" clears refinements, not the user's current query/location.
 */
export function resetSearchState(
  current: SearchState,
): SearchState {
  return {
    ...current,
    filters: createEmptySearchFilters(),
    sort: SEARCH_DEFAULTS.sort,
    page: SEARCH_DEFAULTS.page,
  };
}
