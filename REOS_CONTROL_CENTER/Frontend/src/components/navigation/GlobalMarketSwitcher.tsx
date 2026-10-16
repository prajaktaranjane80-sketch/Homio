
/* File: src/components/navigation/GlobalMarketSwitcher.tsx */
"use client";

import MarketSelector from "@/features/f12_globalization/MarketSelector";
import type { MarketId } from "@/features/f12_globalization/market-activation.types";

type Props = Readonly<{
  value: MarketId;
  onChange: (marketId: MarketId) => void;
  disabled?: boolean;
}>;

export default function GlobalMarketSwitcher({
  value,
  onChange,
  disabled = false,
}: Props) {
  return (
    <MarketSelector
      value={value}
      onChange={onChange}
      disabled={disabled}
      label="Global market"
    />
  );
}
