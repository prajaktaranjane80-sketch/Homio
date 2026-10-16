
export type MarketId =
  | "pune-in"
  | "dubai-ae"
  | "singapore-sg"
  | "tokyo-jp"
  | "london-gb"
  | "new-york-us";

export type MarketActivationState = "ACTIVE" | "BUILT";

export type MarketServiceConnection =
  | "REQUIRES_VERIFICATION"
  | "NOT_ACTIVE";

export type MarketCapabilityKey =
  | "inventory"
  | "search"
  | "enquiry"
  | "visit"
  | "brokerage"
  | "dealFlow"
  | "operationalServices";

export type CurrencyCode =
  | "INR"
  | "AED"
  | "SGD"
  | "JPY"
  | "GBP"
  | "USD";

export type AreaUnit = "sqft" | "sqm";

export type MarketDefinition = Readonly<{
  id: MarketId;
  city: string;
  country: string;
  countryCode: string;
  displayName: string;
  currency: CurrencyCode;
  areaUnit: AreaUnit;
  supportedLanguages: readonly string[];
  activationState: MarketActivationState;
  serviceConnection: MarketServiceConnection;

  /**
   * Capabilities permitted by the market's activation policy.
   * This is not evidence of live service availability or user permission.
   */
  policyEnabledCapabilities: readonly MarketCapabilityKey[];
}>;

export type MarketAvailability = Readonly<{
  marketId: MarketId | null;
  activationState: MarketActivationState | "UNKNOWN";
  label: string;
  title: string;
  description: string;
  serviceDisclosure: string;
  operationallyAvailable: false;
}>;

export type MarketOption = Readonly<{
  value: MarketId;
  label: string;
  description: string;
}>;

export type CurrencyOption = Readonly<{
  value: CurrencyCode;
  label: string;
  symbol: string;
}>;

export type AreaUnitOption = Readonly<{
  value: AreaUnit;
  label: string;
  shortLabel: string;
}>;
