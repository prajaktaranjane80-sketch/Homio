import HomeDiscoveryPage from "@/features/f02_home_discovery/HomeDiscoveryPage";
import { createSeoMetadata } from "@/features/f13_production/SeoMetadata";

export const metadata = createSeoMetadata({
  title: "Global Property Discovery",
  description:
    "Explore HOMIO homes, rentals, commercial spaces and project experience previews. Listing facts and availability remain subject to source verification.",
  path: "/",
  // Current home sections contain experience-preview records, not verified inventory.
  noIndex: true,
});

export default function HomePage() {
  return <HomeDiscoveryPage />;
}
