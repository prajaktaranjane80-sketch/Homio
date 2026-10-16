
/* File: src/components/system/ComingSoonState.tsx */
import MarketComingSoon from "@/features/f12_globalization/MarketComingSoon";
import type { MarketId } from "@/features/f12_globalization/market-activation.types";

type Props = Readonly<{
  marketId: MarketId;
  description?: string;
}>;

export default function ComingSoonState(props: Props) {
  return <MarketComingSoon {...props} />;
}
