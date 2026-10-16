
import type { ReactNode } from "react";

import MarketUnavailableState from "./MarketUnavailableState";

import { getMarketById } from "./market-activation.utils";

import type { MarketCapabilityKey } from "./market-activation.types";

type MarketFeatureGateProps = Readonly<{
  marketId: string;
  capability: MarketCapabilityKey;

  /**
   * Display status supplied by the trusted server-side integration layer.
   * This UI prop is not an authorization mechanism.
   */
  serviceVerified?: boolean;

  children: ReactNode;
  fallback?: ReactNode;
  title?: string;
  description?: string;
}>;

/**
 * Presentational gate for market-specific features.
 *
 * APIs, server actions and data loaders must enforce their own
 * authentication, role permissions and record-level authorization.
 * A browser can alter UI props; this component must never be used
 * as a security boundary.
 */
export default function MarketFeatureGate({
  marketId,
  capability,
  serviceVerified = false,
  children,
  fallback,
  title,
  description,
}: MarketFeatureGateProps) {
  const market = getMarketById(marketId);

  const marketPolicyAllows =
    market?.activationState === "ACTIVE" &&
    market.policyEnabledCapabilities.includes(capability);

  const canDisplayFeature =
    marketPolicyAllows && serviceVerified;

  if (canDisplayFeature) {
    return <>{children}</>;
  }

  if (fallback) {
    return <>{fallback}</>;
  }

  if (!market) {
    return (
      <MarketUnavailableState
        title="Market not configured"
        description="This market is not part of the configured HOMIO market registry. Select a configured market or complete the approved market setup."
        eyebrow="MARKET CONFIGURATION"
      />
    );
  }

  if (!marketPolicyAllows) {
    return (
      <MarketUnavailableState
        title={title ?? `${market.city} is not operationally active`}
        description={
          description ??
          "This market is prepared for future activation. The requested capability remains unavailable until the market policy and relevant REOS service are approved."
        }
        eyebrow="CAPABILITY NOT ACTIVE"
        marketName={market.displayName}
      />
    );
  }

  return (
    <MarketUnavailableState
      title={title ?? "Service connection not verified"}
      description={
        description ??
        "The market activation policy is enabled, but the relevant business service has not been verified as operational. This workspace remains unavailable until its approved integration is connected."
      }
      eyebrow="SERVICE VERIFICATION REQUIRED"
      marketName={market.displayName}
    />
  );
}
