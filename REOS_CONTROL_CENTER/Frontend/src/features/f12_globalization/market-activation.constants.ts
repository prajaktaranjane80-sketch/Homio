
import type {
  AreaUnitOption,
  CurrencyOption,
  MarketCapabilityKey,
  MarketDefinition,
  MarketId,
} from "./market-activation.types";

export const DEFAULT_MARKET_ID: MarketId = "pune-in";

export const MARKET_CAPABILITIES: readonly MarketCapabilityKey[] = [
  "inventory",
  "search",
  "enquiry",
  "visit",
  "brokerage",
  "dealFlow",
  "operationalServices",
];

export const MARKET_DEFINITIONS: readonly MarketDefinition[] = [
  {
    id: "pune-in",
    city: "Pune",
    country: "India",
    countryCode: "IN",
    displayName: "Pune, India",
    currency: "INR",
    areaUnit: "sqft",
    supportedLanguages: ["English", "Marathi", "Hindi"],
    activationState: "ACTIVE",
    serviceConnection: "REQUIRES_VERIFICATION",
    policyEnabledCapabilities: MARKET_CAPABILITIES,
  },
  {
    id: "dubai-ae",
    city: "Dubai",
    country: "United Arab Emirates",
    countryCode: "AE",
    displayName: "Dubai, UAE",
    currency: "AED",
    areaUnit: "sqm",
    supportedLanguages: ["English", "Arabic"],
    activationState: "BUILT",
    serviceConnection: "NOT_ACTIVE",
    policyEnabledCapabilities: [],
  },
  {
    id: "singapore-sg",
    city: "Singapore",
    country: "Singapore",
    countryCode: "SG",
    displayName: "Singapore",
    currency: "SGD",
    areaUnit: "sqm",
    supportedLanguages: ["English"],
    activationState: "BUILT",
    serviceConnection: "NOT_ACTIVE",
    policyEnabledCapabilities: [],
  },
  {
    id: "tokyo-jp",
    city: "Tokyo",
    country: "Japan",
    countryCode: "JP",
    displayName: "Tokyo, Japan",
    currency: "JPY",
    areaUnit: "sqm",
    supportedLanguages: ["Japanese", "English"],
    activationState: "BUILT",
    serviceConnection: "NOT_ACTIVE",
    policyEnabledCapabilities: [],
  },
  {
    id: "london-gb",
    city: "London",
    country: "United Kingdom",
    countryCode: "GB",
    displayName: "London, UK",
    currency: "GBP",
    areaUnit: "sqft",
    supportedLanguages: ["English"],
    activationState: "BUILT",
    serviceConnection: "NOT_ACTIVE",
    policyEnabledCapabilities: [],
  },
  {
    id: "new-york-us",
    city: "New York",
    country: "United States",
    countryCode: "US",
    displayName: "New York, USA",
    currency: "USD",
    areaUnit: "sqft",
    supportedLanguages: ["English"],
    activationState: "BUILT",
    serviceConnection: "NOT_ACTIVE",
    policyEnabledCapabilities: [],
  },
];

export const CURRENCY_OPTIONS: readonly CurrencyOption[] = [
  { value: "INR", label: "Indian Rupee", symbol: "₹" },
  { value: "AED", label: "UAE Dirham", symbol: "د.إ" },
  { value: "SGD", label: "Singapore Dollar", symbol: "S$" },
  { value: "JPY", label: "Japanese Yen", symbol: "¥" },
  { value: "GBP", label: "British Pound", symbol: "£" },
  { value: "USD", label: "US Dollar", symbol: "$" },
];

export const AREA_UNIT_OPTIONS: readonly AreaUnitOption[] = [
  {
    value: "sqft",
    label: "Square feet",
    shortLabel: "sq ft",
  },
  {
    value: "sqm",
    label: "Square metres",
    shortLabel: "m²",
  },
];

export const LANGUAGE_OPTIONS: readonly string[] = [
  "English",
  "Marathi",
  "Hindi",
  "Arabic",
  "Japanese",
];

export const COUNTRY_OPTIONS = Array.from(
  new Map(
    MARKET_DEFINITIONS.map((market) => [
      market.countryCode,
      {
        value: market.countryCode,
        label: market.country,
      },
    ]),
  ).values(),
);

export const MARKET_OPTIONS = MARKET_DEFINITIONS.map((market) => ({
  value: market.id,
  label: market.displayName,
  description:
    market.activationState === "ACTIVE"
      ? "Designated active market"
      : "Built for future activation",
}));
