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

export default function CompareProperties({
  items,
  selectedGroups,
  onRemove,
}: Props) {
  const properties = items.filter(
    (item) => item.kind === "property",
  );

  if (properties.length === 0) {
    return (
      <CompareEmptyState
        title="No properties in this comparison"
        description="Add properties from HOMIO discovery to compare their supplied facts."
      />
    );
  }

  return (
    <CompareTable
      items={properties}
      selectedGroups={selectedGroups}
      onRemove={onRemove}
    />
  );
}
