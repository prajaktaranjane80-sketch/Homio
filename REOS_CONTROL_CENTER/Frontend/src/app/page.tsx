import HomeHeader from "@/components/home/HomeHeader";
import HomeSecondaryNav from "@/components/home/HomeSecondaryNav";
import HomeHero from "@/components/home/HomeHero";
import HomeQuickDiscovery from "@/components/home/HomeQuickDiscovery";
import PopularCities from "@/components/home/PopularCities";
import PopularLocalities from "@/components/home/PopularLocalities";
import FeaturedProjects from "@/components/home/FeaturedProjects";
import NewProjectCollections from "@/components/home/NewProjectCollections";
import FreshProperties from "@/components/home/FreshProperties";
import OwnerProperties from "@/components/home/OwnerProperties";
import VerifiedProperties from "@/components/home/VerifiedProperties";
import PropertyCollections from "@/components/home/PropertyCollections";
import CommercialSection from "@/components/home/CommercialSection";
import ResidentialCollections from "@/components/home/ResidentialCollections";
import RentalSection from "@/components/home/RentalSection";
import PlotLandSection from "@/components/home/PlotLandSection";
import PropertyTools from "@/components/home/PropertyTools";
import MarketIntelligence from "@/components/home/MarketIntelligence";
import HomioAdvice from "@/components/home/HomioAdvice";
import HomeServices from "@/components/home/HomeServices";
import BuilderProjects from "@/components/home/BuilderProjects";
import SaveCompareSection from "@/components/home/SaveCompareSection";
import HomioAISection from "@/components/home/HomioAISection";
import BrokerageCTA from "@/components/home/BrokerageCTA";
import PostPropertySection from "@/components/home/PostPropertySection";
import WhyHomio from "@/components/home/WhyHomio";
import TrustSection from "@/components/home/TrustSection";
import MyHomioSection from "@/components/home/MyHomioSection";
import HelpSupport from "@/components/home/HelpSupport";
import HomeFooter from "@/components/home/HomeFooter";

export default function HomePage() {
  return (
    <>
      <HomeHeader />

      <HomeSecondaryNav />

      <main>
        {/* LP03 — Hero / Search */}
        <HomeHero />

        {/* LP04 — Quick Discovery */}
        <HomeQuickDiscovery />

        {/* LP05 — Global Cities */}
        <PopularCities />

        {/* LP06 — Popular Localities */}
        <PopularLocalities />

        {/* LP07 — Featured Projects */}
        <FeaturedProjects />

        {/* LP08 — New Project Collections */}
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

        {/* LP15 — Rental */}
        <RentalSection />

        {/* LP16 — Plots & Land */}
        <PlotLandSection />

        {/* LP17 — Property Tools */}
        <PropertyTools />

        {/* LP18 — Market Intelligence */}
        <MarketIntelligence />

        {/* LP19 — HOMIO Advice */}
        <HomioAdvice />

        {/* LP20 — HOMIO Services */}
        <HomeServices />

        {/* LP21 — Builder Projects */}
        <BuilderProjects />

        {/* LP22 — Save & Compare */}
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

        {/* LP29 — Help & Support */}
        <HelpSupport />
      </main>

      {/* LP30 — Footer */}
      <HomeFooter />
    </>
  );
}
