import SearchSuggestionGroup from "./SearchSuggestionGroup";
import type { SearchSuggestion } from "./SearchExperience.types";

type Props = Readonly<{
  locations: readonly SearchSuggestion[];
  onSelect?: (item: SearchSuggestion) => void;
}>;

export default function SearchLocationSuggestion({ locations, onSelect }: Props) {
  const validLocations = locations.filter((item) => item.kind === "location");

  return (
    <SearchSuggestionGroup
      heading="Locations"
      suggestions={validLocations}
      onSelect={onSelect}
    />
  );
}
