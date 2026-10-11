import HomeSecondaryNav from "./HomeSecondaryNav";
import HomeHero from "./HomeHero";
import HomeQuickDiscovery from "./HomeQuickDiscovery";
import PopularCities from "./PopularCities";
import PopularLocalities from "./PopularLocalities";
import FeaturedProjects from "./FeaturedProjects";
import NewProjectCollections from "./NewProjectCollections";
import FreshProperties from "./FreshProperties";
import OwnerProperties from "./OwnerProperties";
import VerifiedProperties from "./VerifiedProperties";
import PropertyCollections from "./PropertyCollections";
import CommercialSection from "./CommercialSection";
import ResidentialCollections from "./ResidentialCollections";
import RentalSection from "./RentalSection";
import PlotLandSection from "./PlotLandSection";
import PropertyTools from "./PropertyTools";
import MarketIntelligence from "./MarketIntelligence";
import HomioAdvice from "./HomioAdvice";
import HomeServices from "./HomeServices";
import BuilderProjects from "./BuilderProjects";
import SaveCompareSection from "./SaveCompareSection";
import HomioAISection from "./HomioAISection";
import BrokerageCTA from "./BrokerageCTA";
import PostPropertySection from "./PostPropertySection";
import WhyHomio from "./WhyHomio";
import TrustSection from "./TrustSection";
import MyHomioSection from "./MyHomioSection";
import HelpSupport from "./HelpSupport";
import HomeFooter from "./HomeFooter";

export default function HomeDiscoveryPage() {
  return (
    <>
      <HomeSecondaryNav />

      <main>
        {/* LP03 — Hero / Search */}
        <HomeHero />

        {/* LP04 — Quick Discovery */}
        <HomeQuickDiscovery />

        {/* LP05 — Cities */}
        <PopularCities />

        {/* LP06 — Localities */}
        <PopularLocalities />

        {/* LP07 — Featured Projects */}
        <FeaturedProjects />

        {/* LP08 — Project Collections */}
        <NewProjectCollections />

        {/* LP09 — Fresh Properties */}
        <FreshProperties />

        {/* LP10 — Owner Properties */}
        <OwnerProperties />

        {/* LP11 — Verified Properties */}
        <VerifiedProperties />

        {/* LP12 — Property Collections */}
        <PropertyCollections />

        {/* LP13 — Commercial */}
        <CommercialSection />

        {/* LP14 — Residential */}
        <ResidentialCollections />

        {/* LP15 — Rentals */}
        <RentalSection />

        {/* LP16 — Plots and Land */}
        <PlotLandSection />

        {/* LP17 — Property Tools */}
        <PropertyTools />

        {/* LP18 — Market Intelligence */}
        <MarketIntelligence />

        {/* LP19 — HOMIO Advice */}
        <HomioAdvice />

        {/* LP20 — Home Services */}
        <HomeServices />

        {/* LP21 — Builder Projects */}
        <BuilderProjects />

        {/* LP22 — Save and Compare */}
        <SaveCompareSection />

        {/* LP23 — HOMIO AI */}
        <HomioAISection />

        {/* LP24 — HOMIO Brokerage */}
        <BrokerageCTA />

        {/* LP25 — Post Property */}
        <PostPropertySection />

        {/* LP26 — Why HOMIO */}
        <WhyHomio />

        {/* LP27 — Trust */}
        <TrustSection />

        {/* LP28 — My HOMIO */}
        <MyHomioSection />

        {/* LP29 — Help and Support */}
        <HelpSupport />
      </main>

      {/* LP30 — Footer */}
      <HomeFooter />
    </>
  );
}