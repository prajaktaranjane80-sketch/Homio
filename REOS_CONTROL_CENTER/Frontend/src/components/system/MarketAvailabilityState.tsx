
/* File: src/components/system/MarketAvailabilityState.tsx */
import MarketAvailabilityNotice from "@/features/f12_globalization/MarketAvailabilityNotice";
import MarketUnavailableState from "@/features/f12_globalization/MarketUnavailableState";
import { getMarketAvailability } from "@/features/f12_globalization/market-activation.utils";

type Props = Readonly<{
  marketId: string;
  compact?: boolean;
}>;

export default function MarketAvailabilityState({
  marketId,
  compact = false,
}: Props) {
  const availability = getMarketAvailability(marketId);

  if (availability.activationState === "ACTIVE" && availability.marketId) {
    return (
      <MarketAvailabilityNotice
        marketId={availability.marketId}
        compact={compact}
      />
    );
  }

  return (
    <MarketUnavailableState
      title={availability.title}
      description={availability.description}
      eyebrow="MARKET AVAILABILITY"
      marketName={marketId}
      compact={compact}
    />
  );
}
