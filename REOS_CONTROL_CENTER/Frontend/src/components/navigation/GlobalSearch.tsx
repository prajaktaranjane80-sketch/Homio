"use client";

import { useRouter } from "next/navigation";
import { useId, useState } from "react";
import type { FormEvent } from "react";

import { Button } from "@/components/ui/Button";
import { SearchField } from "@/components/ui/SearchField";

export function GlobalSearch({
  onSubmitQuery,
  disabled = false,
}: {
  onSubmitQuery?: (query: string) => void;
  disabled?: boolean;
}) {
  const router = useRouter();
  const statusId = useId();
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("");

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const normalized = query.trim();

    if (!normalized) {
      setStatus("Enter a property, project or location to search.");
      return;
    }

    if (onSubmitQuery) {
      setStatus("");
      onSubmitQuery(normalized);
      return;
    }

    const params = new URLSearchParams({ q: normalized });

    setStatus("");
    router.push(`/search?${params.toString()}`);
  }

  return (
    <div className="global-search">
      <form className="global-search__form" onSubmit={submit} noValidate>
        <SearchField
          aria-label="Search HOMIO"
          aria-invalid={status ? true : undefined}
          aria-describedby={status ? statusId : undefined}
          name="q"
          placeholder="Search homes, projects or locations"
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

      <div
        id={statusId}
        className="global-search__status"
        role="status"
        aria-live="polite"
      >
        {status}
      </div>
    </div>
  );
}
