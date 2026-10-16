
import {
  DEFAULT_MARKET_ID,
  MARKET_DEFINITIONS,
} from "./market-activation.constants";

import type {
  MarketAvailability,
  MarketCapabilityKey,
  MarketDefinition,
  MarketId,
} from "./market-activation.types";

export function isMarketId(value: string): value is MarketId {
  return MARKET_DEFINITIONS.some((market) => market.id === value);
}

export function getMarketById(
  marketId: string | null | undefined,
): MarketDefinition | undefined {
  if (!marketId) {
    return undefined;
  }

  return MARKET_DEFINITIONS.find((market) => market.id === marketId);
}

export function normalizeMarketId(
  marketId: string | null | undefined,
): MarketId {
  return marketId && isMarketId(marketId)
    ? marketId
    : DEFAULT_MARKET_ID;
}

export function getMarketAvailability(
  marketId: string | null | undefined,
): MarketAvailability {
  const market = getMarketById(marketId);

  if (!market) {
    return {
      marketId: null,
      activationState: "UNKNOWN",
      label: "Market not configured",
      title: "This market is not configured in HOMIO",
      description:
        "Choose one of the configured markets to see its activation policy.",
      serviceDisclosure:
        "No live inventory or business operation is available through an unknown market selection.",
      operationallyAvailable: false,
    };
  }

  if (market.activationState === "ACTIVE") {
    return {
      marketId: market.id,
      activationState: "ACTIVE",
      label: "Active market policy",
      title: `${market.city} is the designated active market`,
      description:
        "The market activation policy is enabled for this location. Individual business capabilities still require their own approved REOS service connections.",
      serviceDisclosure:
        "Market activation does not confirm live inventory, completed brokerage setup, booked visits or operational deal flow. Each service must be verified independently.",
      operationallyAvailable: false,
    };
  }

  return {
    marketId: market.id,
    activationState: "BUILT",
    label: "Built · not operational",
    title: `${market.city} is prepared for future activation`,
    description:
      "The market selection experience is configured, but the market is not operationally active.",
    serviceDisclosure:
      "Live inventory operations, enquiry and visit execution, brokerage activity, deal flow and other operational services remain unavailable until formally activated.",
    operationallyAvailable: false,
  };
}

/**
 * Presentation-policy check only.
 *
 * The verifiedCapabilities argument must never come from an untrusted
 * browser value to authorize an operation. Real permission checks must
 * happen on the server through the approved REOS capability.
 */
export function isCapabilityOperational(
  marketId: string | null | undefined,
  capability: MarketCapabilityKey,
  verifiedCapabilities: readonly MarketCapabilityKey[] = [],
): boolean {
  const market = getMarketById(marketId);

  if (!market || market.activationState !== "ACTIVE") {
    return false;
  }

  if (!market.policyEnabledCapabilities.includes(capability)) {
    return false;
  }

  return verifiedCapabilities.includes(capability);
}

export function getMarketStatusLabel(
  marketId: string | null | undefined,
): string {
  const market = getMarketById(marketId);

  if (!market) {
    return "Unknown market";
  }

  return market.activationState === "ACTIVE"
    ? "ACTIVE MARKET"
    : "BUILT · NOT LIVE";
}
