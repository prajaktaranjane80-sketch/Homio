
/* File: src/components/system/NoResults.tsx */
import type { ReactNode } from "react";

import { EmptyState } from "@/components/ui/EmptyState";

type Props = Readonly<{
  query?: string;
  description?: string;
  onClear?: () => void;
}>;

export default function NoResults({
  query,
  description,
  onClear,
}: Props) {
  const detail =
    description ??
    (query?.trim()
      ? `No matching results were returned for “${query.trim()}”.`
      : "No matching results were returned. Try changing your criteria.");

  const action: ReactNode = onClear ? (
    <button type="button" onClick={onClear}>
      Clear filters
    </button>
  ) : null;

  return (
    <EmptyState
      title="Nothing matches this search"
      description={detail}
      action={action}
    />
  );
}
