import type {
  CompareFieldGroup,
  CompareItem,
} from "./compare.types";

import CompareEmptyState from "./CompareEmptyState";
import CompareTable from "./CompareTable";

type Props = Readonly<{
  items: readonly CompareItem[];
  selectedGroups: readonly CompareFieldGroup[];

  onRemove?: (
    id: string,
    kind: CompareItem["kind"],
  ) => void;
}>;

export default function CompareProjects({
  items,
  selectedGroups,
  onRemove,
}: Props) {
  const projects = items.filter(
    (item) => item.kind === "project",
  );

  if (projects.length === 0) {
    return (
      <CompareEmptyState
        title="No projects in this comparison"
        description="Add projects from HOMIO discovery. Unverified inventory and availability are not inferred."
      />
    );
  }

  return (
    <CompareTable
      items={projects}
      selectedGroups={selectedGroups}
      onRemove={onRemove}
    />
  );
}
