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

export default function CompareLocalities({
  items,
  selectedGroups,
  onRemove,
}: Props) {
  const localities = items.filter(
    (item) => item.kind === "locality",
  );

  if (localities.length === 0) {
    return (
      <CompareEmptyState
        title="No locations in this comparison"
        description="Location comparisons use only facts supplied by the source adapter."
      />
    );
  }

  return (
    <CompareTable
      items={localities}
      selectedGroups={selectedGroups}
      onRemove={onRemove}
    />
  );
}
