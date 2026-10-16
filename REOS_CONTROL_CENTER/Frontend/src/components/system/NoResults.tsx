import type { ReactNode } from "react";

import { EmptyResults } from "./EmptyResults";

type Props = Readonly<{
  searchTerm?: string;
  title?: string;
  description?: string;
  action?: ReactNode;
}>;

export function NoResults({
  searchTerm,
  title = "No matching results",
  description,
  action,
}: Props) {
  const detail =
    description ??
    (searchTerm?.trim()
      ? `No results were returned for “${searchTerm.trim()}”. Try a broader search or remove a filter.`
      : "Try changing your search criteria or clearing selected filters.");

  return <EmptyResults title={title} description={detail} action={action} />;
}
