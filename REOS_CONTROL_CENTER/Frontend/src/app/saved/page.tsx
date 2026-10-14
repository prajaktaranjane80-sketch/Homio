"use client";

import SavedShell from "@/features/f06_save_compare/SavedShell";

import {
  removeSavedRecord,
  useSaveCompareSession,
} from "@/features/f06_save_compare/saveCompareSession";

export default function SavedPage() {
  const { savedRecords } = useSaveCompareSession();

  return (
    <SavedShell
      records={savedRecords}
      persistenceStatus="session-only"
      onRemoveRecord={(id, kind) =>
        removeSavedRecord(id, kind)
      }
    />
  );
}
