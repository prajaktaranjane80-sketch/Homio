import HomeDiscoveryPage from "@/features/f02_home_discovery/HomeDiscoveryPage";
import { createSeoMetadata } from "@/features/f13_production/SeoMetadata";

export const metadata = createSeoMetadata({
  title: "Pune Property Discovery",
  description:
    "Start a Pune-focused HOMIO search for homes, rentals, projects and commercial spaces. Preview content is not authoritative inventory; property facts and availability remain subject to source verification.",
  path: "/",
  noIndex: true,
});

export default function HomePage() {
  return <HomeDiscoveryPage />;
}
