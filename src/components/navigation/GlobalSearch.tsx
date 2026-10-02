"use client";

import { FormEvent, useState } from "react";

import { SearchField } from "@/components/ui/SearchField";
import { Button } from "@/components/ui/Button";

export function GlobalSearch({
  onSubmitQuery,
  disabled = false,
}: {
  onSubmitQuery?: (query: string) => void;
  disabled?: boolean;
}) {
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("");

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const normalized = query.trim();

    if (!normalized) {
      setStatus("Enter a real-estate search intent.");
      return;
    }

    if (onSubmitQuery) {
      setStatus("");
      onSubmitQuery(normalized);
      return;
    }

    setStatus("Search binding will activate in F03.");
  }

  return (
    <div className="global-search">
      <form className="global-search__form" onSubmit={submit} noValidate>
        <SearchField
          aria-label="Search HOMIO"
          placeholder="Search HOMIO by property, place or intent"
          value={query}
          onChange={(event) => {
            setQuery(event.target.value);
            if (status) {
              setStatus("");
            }
          }}
          disabled={disabled}
        />

        <Button
          type="submit"
          variant="secondary"
          size="small"
          disabled={disabled}
        >
          Search
        </Button>
      </form>

      <div className="global-search__status" aria-live="polite">
        {status}
      </div>
    </div>
  );
}
