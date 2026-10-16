
/* File: src/components/navigation/MarketsMenu.tsx */
import MegaMenuPanel from "./MegaMenuPanel";

import { MARKET_DEFINITIONS } from "@/features/f12_globalization/market-activation.constants";

export default function MarketsMenu() {
  const items = MARKET_DEFINITIONS.map((market) => ({
    label: market.displayName,
    description:
      market.activationState === "ACTIVE"
        ? "Active market policy; service readiness is checked separately."
        : "Configured for future activation; not operationally active.",
    href:
      market.activationState === "ACTIVE"
        ? `/search?city=${encodeURIComponent(market.city)}`
        : undefined,
    disabled: market.activationState !== "ACTIVE",
    badge:
      market.activationState === "ACTIVE"
        ? "ACTIVE POLICY"
        : "BUILT · NOT LIVE",
  }));

  return (
    <MegaMenuPanel
      eyebrow="GLOBAL REACH"
      title="Markets"
      description="Select from configured destinations. Availability depends on activation and verified services."
      items={items}
    />
  );
}
