import type { CompareFieldGroup, CompareItem } from "./compare.types";
import CompareEmptyState from "./CompareEmptyState";
import CompareTable from "./CompareTable";

type Props = Readonly<{ items: readonly CompareItem[]; selectedGroups: readonly CompareFieldGroup[]; onRemove?: (id: string) => void }>;
export default function CompareProperties({ items, selectedGroups, onRemove }: Props) {
  const selected = items.filter((item) => item.kind === "property");
  if (!selected.length) return <CompareEmptyState title="No properties in this comparison" description="Add properties from a connected HOMIO search or property experience to compare their supplied facts." />;
  return <CompareTable items={selected} selectedGroups={selectedGroups} onRemove={onRemove} />;
}
