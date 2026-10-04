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

export default function HomePage() {
  return (
    <>
      <HomeHeader />
      <HomeSecondaryNav />

      <main>
        <HomeHero />

        <HomeQuickDiscovery />

        <PopularCities />

        <PopularLocalities />

        <FeaturedProjects />

        <NewProjectCollections />

        <FreshProperties />

        <OwnerProperties />

        <VerifiedProperties />

        <PropertyCollections />

        <CommercialSection />

        <ResidentialCollections />

        <RentalSection />

        <PlotLandSection />

        <PropertyTools />

        <MarketIntelligence />

        <HomioAdvice />

        <HomeServices />

        <BuilderProjects />

        <section id="post-property" className="homio-section">
          <div className="homio-container">
            <h2>List a property with HOMIO</h2>
          </div>
        </section>
      </main>
    </>
  );
}
