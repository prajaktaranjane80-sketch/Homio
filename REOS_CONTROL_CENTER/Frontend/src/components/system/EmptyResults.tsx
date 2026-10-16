
/* File: src/components/system/EmptyResults.tsx */
import type { ReactNode } from "react";

import { EmptyState } from "@/components/ui/EmptyState";

type Props = Readonly<{
  title?: string;
  description: string;
  action?: ReactNode;
}>;

export default function EmptyResults({
  title = "No results to show",
  description,
  action,
}: Props) {
  return (
    <EmptyState
      title={title}
      description={description}
      action={action}
    />
  );
}
