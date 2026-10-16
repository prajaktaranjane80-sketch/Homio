import SearchSuggestionGroup from "./SearchSuggestionGroup";
import type { SearchSuggestion } from "./SearchExperience.types";

type Props = Readonly<{
  projects: readonly SearchSuggestion[];
  onSelect?: (item: SearchSuggestion) => void;
}>;

export default function SearchProjectSuggestion({ projects, onSelect }: Props) {
  const validProjects = projects.filter((item) => item.kind === "project");

  return (
    <SearchSuggestionGroup
      heading="Projects"
      suggestions={validProjects}
      onSelect={onSelect}
    />
  );
}
