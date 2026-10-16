import SearchSuggestionGroup from "./SearchSuggestionGroup";
import type { SearchSuggestion } from "./SearchExperience.types";

type Props = Readonly<{
  items: readonly SearchSuggestion[];
  onSelect?: (item: SearchSuggestion) => void;
}>;

export default function SearchPopularItem({ items, onSelect }: Props) {
  const popularItems = items.filter((item) => item.kind === "popular");

  return (
    <SearchSuggestionGroup
      heading="Popular searches"
      suggestions={popularItems}
      onSelect={onSelect}
    />
  );
}
