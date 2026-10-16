import SearchSuggestionGroup from "./SearchSuggestionGroup";
import type { SearchSuggestion } from "./SearchExperience.types";

type Props = Readonly<{
  properties: readonly SearchSuggestion[];
  onSelect?: (item: SearchSuggestion) => void;
}>;

export default function SearchPropertySuggestion({ properties, onSelect }: Props) {
  const validProperties = properties.filter((item) => item.kind === "property");

  return (
    <SearchSuggestionGroup
      heading="Properties"
      suggestions={validProperties}
      onSelect={onSelect}
    />
  );
}
