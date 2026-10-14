"use client";

import CompareShell from "@/features/f06_save_compare/CompareShell";

import {
  clearComparedItems,
  removeComparedItem,
  useSaveCompareSession,
} from "@/features/f06_save_compare/saveCompareSession";

export default function ComparePage() {
  const { comparedItems } = useSaveCompareSession();

  return (
    <CompareShell
      items={comparedItems}
      onRemove={(id, kind) =>
        removeComparedItem(id, kind)
      }
      onClear={clearComparedItems}
    />
  );
}
