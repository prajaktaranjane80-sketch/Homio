import {
  SEARCH_FURNISHING_OPTIONS,
  SEARCH_POSSESSION_OPTIONS,
  SEARCH_PROPERTY_STATUSES,
} from "./search.constants";

import { getAllPropertyPreviews } from "@/features/f04_property/property-preview-catalog";
import { getAllProjectPreviews } from "@/features/f05_project/project-preview-catalog";

import type { PropertyRecord } from "@/features/f04_property/property.types";
import type { ProjectRecord } from "@/features/f05_project/project.types";

import type { SearchResultCardData } from "./SearchResultCard";
import type {
  SearchCurrency,
  SearchIntent,
  SearchState,
} from "./search.types";

const CURRENCY_BY_COUNTRY: Record<string, SearchCurrency> = {
  India: "INR",
  "United Arab Emirates": "AED",
  Singapore: "SGD",
  Japan: "JPY",
};

/**
 * These are explicitly illustrative stock images retained from the current F03
 * experience preview. They are never represented as verified property photos.
 */
const ILLUSTRATIVE_IMAGES: Record<string, string> = {
  "pune-kalyani-nagar-001":
    "https://images.unsplash.com/photo-1600607687920-4e2a09cf159d?auto=format&fit=crop&w=1200&q=80",
  "pune-koregaon-park-002":
    "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=1200&q=80",
  "pune-baner-003":
    "https://images.unsplash.com/photo-1600566753086-00f18fb6b3ea?auto=format&fit=crop&w=1200&q=80",
  "pune-viman-nagar-004":
    "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?auto=format&fit=crop&w=1200&q=80",
  "pune-wakad-005":
    "https://images.unsplash.com/photo-1600607688969-a5bfcd646154?auto=format&fit=crop&w=1200&q=80",
  "pune-hinjewadi-006":
    "https://images.unsplash.com/photo-1600566753190-17f0baa2a6c3?auto=format&fit=crop&w=1200&q=80",
  "pune-magarpattacity-007":
    "https://images.unsplash.com/photo-1600607687920-4e2a09cf159d?auto=format&fit=crop&w=1200&q=80",
  "pune-aundh-008":
    "https://images.unsplash.com/photo-1600585152915-d208bec867a1?auto=format&fit=crop&w=1200&q=80",
};

type ParsedPrice = {
  value?: number;
  currency?: SearchCurrency;
  period: "total" | "monthly";
};

export function parsePreviewPrice(
  price: string,
  country: string,
): ParsedPrice {
  const explicitCurrency = price.match(/\b(AED|SGD|JPY)\b/i)?.[1]
    ?.toUpperCase();

  const currency: SearchCurrency | undefined =
    price.includes("₹")
      ? "INR"
      : explicitCurrency === "AED" ||
          explicitCurrency === "SGD" ||
          explicitCurrency === "JPY"
        ? explicitCurrency
        : CURRENCY_BY_COUNTRY[country];

  const period = /\/\s*month|per month|monthly rent/i.test(price)
    ? "monthly"
    : "total";

  const amountMatch = price.match(
    /(\d[\d,]*(?:\.\d+)?)\s*(crore|cr|lakhs?|million|m)?/i,
  );

  if (!amountMatch || !currency) {
    return { currency, period };
  }

  const rawAmount = Number(amountMatch[1].replace(/,/g, ""));

  if (!Number.isFinite(rawAmount) || rawAmount < 0) {
    return { currency, period };
  }

  const unit = (amountMatch[2] ?? "").toLowerCase();

  let multiplier = 1;

  if (unit === "cr" || unit === "crore") {
    multiplier = 10_000_000;
  } else if (unit === "lakh" || unit === "lakhs") {
    multiplier = 100_000;
  } else if (unit === "m" || unit === "million") {
    multiplier = 1_000_000;
  }

  return {
    value: rawAmount * multiplier,
    currency,
    period,
  };
}

function parseAreaValue(area: string): number | undefined {
  if (/preview information|not supplied/i.test(area)) {
    return undefined;
  }

  const match = area.match(/(\d[\d,]*(?:\.\d+)?)/);

  if (!match) {
    return undefined;
  }

  const value = Number(match[1].replace(/,/g, ""));

  return Number.isFinite(value) && value > 0
    ? value
    : undefined;
}

function normalizeFacet(
  value: string | undefined,
  options: readonly string[],
): string | undefined {
  if (!value) {
    return undefined;
  }

  const normalized = value.trim().toLowerCase();

  return options.find((option) =>
    normalized.startsWith(option.toLowerCase()),
  );
}

function isPlaceholder(value: string): boolean {
  return /preview information|not supplied|not connected|unavailable/i.test(
    value,
  );
}

function toPropertySearchResult(
  property: PropertyRecord,
): SearchResultCardData {
  const parsedPrice = parsePreviewPrice(
    property.price,
    property.country,
  );

  const intent: SearchIntent =
    parsedPrice.period === "monthly" ? "rent" : "buy";

  const amenities = property.amenities
    .filter(
      (item) =>
        item.label.trim().toLowerCase() !== "amenities" &&
        !isPlaceholder(item.label) &&
        !isPlaceholder(item.value),
    )
    .map((item) => item.label);

  return {
    id: property.id,
    entityType: "property",
    intent,
    title: property.title,
    location: property.location,
    locality: property.locality,
    city: property.city,
    country: property.country,
    propertyType: property.propertyType,
    price: property.price,
    priceValue: parsedPrice.value,
    currency: parsedPrice.currency,
    pricePeriod: parsedPrice.period,
    area: property.area,
    areaValue: parseAreaValue(property.area),
    bedrooms: property.bedrooms,
    bathrooms: property.bathrooms,
    image: ILLUSTRATIVE_IMAGES[property.id],
    imageLabel: "Illustrative image — not verified property photography",
    verified: property.verified,
    projectName: property.projectName,
    projectId: property.projectId,
    builderName: property.builderName,
    status: property.status,
    statusFacet: normalizeFacet(
      property.status,
      SEARCH_PROPERTY_STATUSES,
    ),
    furnishingFacet: normalizeFacet(
      property.furnishing,
      SEARCH_FURNISHING_OPTIONS,
    ),
    possessionFacet: normalizeFacet(
      property.possession,
      SEARCH_POSSESSION_OPTIONS,
    ),
    amenities,
    href: `/property/${encodeURIComponent(property.id)}`,
  };
}

function toProjectSearchResult(
  project: ProjectRecord,
): SearchResultCardData {
  const parsedPrice = parsePreviewPrice(
    project.priceFrom,
    project.country,
  );

  return {
    id: project.id,
    entityType: "project",
    intent: "projects",
    title: project.name,
    location: project.location,
    locality: project.locality,
    city: project.city,
    country: project.country,
    propertyType: project.kindLabel,
    price: project.priceFrom,
    priceValue: parsedPrice.value,
    currency: parsedPrice.currency,
    pricePeriod: "total",
    area: project.areaRange,
    areaValue: parseAreaValue(project.areaRange),
    verified: project.verified,
    projectName: project.name,
    status: project.status,
    href: `/project/${encodeURIComponent(project.id)}`,
  };
}

/**
 * The UI uses the shared data adapters; it does not maintain a second copy
 * of the property/project title, price, location or status fields.
 */
export const SEARCH_PREVIEW_CATALOG: SearchResultCardData[] = [
  ...getAllPropertyPreviews().map(toPropertySearchResult),
  ...getAllProjectPreviews().map(toProjectSearchResult),
];

function tokensMatch(haystack: string, query: string): boolean {
  const normalizedHaystack = haystack.toLowerCase();
  const tokens = query
    .trim()
    .toLowerCase()
    .split(/\s+/)
    .filter(Boolean);

  return tokens.every((token) => normalizedHaystack.includes(token));
}

function locationText(item: SearchResultCardData): string {
  return [
    item.location,
    item.locality,
    item.city,
    item.country,
    item.projectName,
  ]
    .filter(Boolean)
    .join(" ");
}

function searchableText(item: SearchResultCardData): string {
  return [
    item.title,
    item.location,
    item.locality,
    item.city,
    item.country,
    item.propertyType,
    item.projectName,
    item.builderName,
    item.status,
  ]
    .filter(Boolean)
    .join(" ");
}

function relevanceScore(
  item: SearchResultCardData,
  query: string,
): number {
  const tokens = query
    .trim()
    .toLowerCase()
    .split(/\s+/)
    .filter(Boolean);

  const title = item.title.toLowerCase();
  const location = locationText(item).toLowerCase();
  const project = (item.projectName ?? "").toLowerCase();

  return tokens.reduce((score, token) => {
    return (
      score +
      (title.includes(token) ? 4 : 0) +
      (project.includes(token) ? 3 : 0) +
      (location.includes(token) ? 2 : 0)
    );
  }, 0);
}

export function filterSearchCatalog(
  catalog: SearchResultCardData[],
  state: SearchState,
): SearchResultCardData[] {
  let results = catalog.filter(
    (item) => item.intent === state.intent,
  );

  if (state.location?.label.trim()) {
    results = results.filter((item) =>
      tokensMatch(locationText(item), state.location!.label),
    );
  }

  if (state.query?.trim()) {
    results = results.filter((item) =>
      tokensMatch(searchableText(item), state.query!),
    );
  }

  /*
   * Project intent is a project/collection search, not a property search.
   * Property-specific filters are deliberately not applied to project cards.
   */
  if (state.intent !== "projects") {
    const filters = state.filters;

    if (filters.propertyTypes.length > 0) {
      results = results.filter((item) =>
        filters.propertyTypes.includes(item.propertyType),
      );
    }

    if (filters.bedrooms.length > 0) {
      results = results.filter(
        (item) =>
          item.bedrooms !== undefined &&
          filters.bedrooms.includes(item.bedrooms),
      );
    }

    if (filters.propertyStatus.length > 0) {
      results = results.filter(
        (item) =>
          item.statusFacet !== undefined &&
          filters.propertyStatus.includes(item.statusFacet),
      );
    }

    if (
      filters.budgetMin !== undefined ||
      filters.budgetMax !== undefined
    ) {
      results = results.filter((item) => {
        if (
          item.currency !== filters.budgetCurrency ||
          item.priceValue === undefined
        ) {
          return false;
        }

        if (
          filters.budgetMin !== undefined &&
          item.priceValue < filters.budgetMin
        ) {
          return false;
        }

        if (
          filters.budgetMax !== undefined &&
          item.priceValue > filters.budgetMax
        ) {
          return false;
        }

        return true;
      });
    }

    if (
      filters.areaMin !== undefined ||
      filters.areaMax !== undefined
    ) {
      results = results.filter((item) => {
        if (item.areaValue === undefined) {
          return false;
        }

        if (
          filters.areaMin !== undefined &&
          item.areaValue < filters.areaMin
        ) {
          return false;
        }

        if (
          filters.areaMax !== undefined &&
          item.areaValue > filters.areaMax
        ) {
          return false;
        }

        return true;
      });
    }

    if (filters.furnishing.length > 0) {
      results = results.filter(
        (item) =>
          item.furnishingFacet !== undefined &&
          filters.furnishing.includes(item.furnishingFacet),
      );
    }

    if (filters.amenities.length > 0) {
      results = results.filter((item) =>
        filters.amenities.every((amenity) =>
          item.amenities?.includes(amenity),
        ),
      );
    }

    if (filters.project?.trim()) {
      results = results.filter((item) =>
        tokensMatch(
          `${item.projectName ?? ""} ${item.title} ${item.projectId ?? ""}`,
          filters.project!,
        ),
      );
    }

    if (filters.builder?.trim()) {
      results = results.filter(
        (item) =>
          item.builderName !== undefined &&
          tokensMatch(item.builderName, filters.builder!),
      );
    }

    if (filters.possession.length > 0) {
      results = results.filter(
        (item) =>
          item.possessionFacet !== undefined &&
          filters.possession.includes(item.possessionFacet),
      );
    }

    if (filters.verifiedOnly) {
      results = results.filter((item) => item.verified === true);
    }
  }

  if (state.sort === "relevance") {
    const relevanceQuery = [
      state.query,
      state.location?.label,
    ]
      .filter(Boolean)
      .join(" ");

    if (relevanceQuery.trim()) {
      results = [...results].sort(
        (a, b) =>
          relevanceScore(b, relevanceQuery) -
          relevanceScore(a, relevanceQuery),
      );
    }
  } else if (
    state.sort === "price_low_to_high" ||
    state.sort === "price_high_to_low"
  ) {
    /*
     * Never compare INR, AED, SGD and JPY as if they were one currency.
     * Unknown/preview-only prices are omitted from price-sorted results.
     */
    results = results
      .filter(
        (item) =>
          item.currency === state.filters.budgetCurrency &&
          item.priceValue !== undefined,
      )
      .sort((a, b) => {
        const left = a.priceValue ?? 0;
        const right = b.priceValue ?? 0;

        return state.sort === "price_low_to_high"
          ? left - right
          : right - left;
      });
  } else if (state.sort === "area_high_to_low") {
    results = [...results].sort(
      (a, b) =>
        (b.areaValue ?? -1) - (a.areaValue ?? -1),
    );
  }

  /*
   * No reliable publish timestamps exist in this preview catalogue.
   * "Newest" therefore preserves catalogue order instead of inventing dates.
   */
  return results;
}
