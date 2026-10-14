import type { CompareFieldGroup, CompareItem } from "./compare.types";
import CompareEmptyState from "./CompareEmptyState";
import CompareTable from "./CompareTable";

type Props = Readonly<{ items: readonly CompareItem[]; selectedGroups: readonly CompareFieldGroup[]; onRemove?: (id: string) => void }>;
export default function CompareLocalities({ items, selectedGroups, onRemove }: Props) {
  const selected = items.filter((item) => item.kind === "locality");
  if (!selected.length) return <CompareEmptyState title="No locations in this comparison" description="Compare location context only when the source adapter supplies those facts for each locality." />;
  return <CompareTable items={selected} selectedGroups={selectedGroups} onRemove={onRemove} />;
}
