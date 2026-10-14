import type { CompareFieldGroup, CompareItem } from "./compare.types";
import CompareEmptyState from "./CompareEmptyState";
import CompareTable from "./CompareTable";

type Props = Readonly<{ items: readonly CompareItem[]; selectedGroups: readonly CompareFieldGroup[]; onRemove?: (id: string) => void }>;
export default function CompareProjects({ items, selectedGroups, onRemove }: Props) {
  const selected = items.filter((item) => item.kind === "project");
  if (!selected.length) return <CompareEmptyState title="No projects in this comparison" description="Projects supplied by the approved project adapter will appear here, with no invented inventory or availability." />;
  return <CompareTable items={selected} selectedGroups={selectedGroups} onRemove={onRemove} />;
}
