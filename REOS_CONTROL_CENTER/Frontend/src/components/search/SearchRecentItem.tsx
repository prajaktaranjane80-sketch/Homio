import SearchSuggestionGroup from "./SearchSuggestionGroup";
import type { SearchSuggestion } from "./SearchExperience.types";

type Props = Readonly<{
  items: readonly SearchSuggestion[];
  onSelect?: (item: SearchSuggestion) => void;
}>;

export default function SearchRecentItem({ items, onSelect }: Props) {
  const recentItems = items.filter((item) => item.kind === "recent");

  return (
    <SearchSuggestionGroup
      heading="Recent searches"
      suggestions={recentItems}
      onSelect={onSelect}
    />
  );
}
