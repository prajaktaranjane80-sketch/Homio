import SearchShell from "@/features/f03_search/SearchShell";
import { createSeoMetadata } from "@/features/f13_production/SeoMetadata";

export const metadata = createSeoMetadata({
  title: "Search Homes, Rentals and Projects",
  description:
    "Explore HOMIO property and project experience previews. Search results are not authoritative inventory until connected to approved source records.",
  path: "/search",
  // Filtered preview results must not be indexed as verified market inventory.
  noIndex: true,
});

export default function SearchRoute() {
  return <SearchShell />;
}
