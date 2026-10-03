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

        <section id="tools" className="homio-section">
          <div className="homio-container">
            <h2>Property tools</h2>
          </div>
        </section>

        <section id="advice" className="homio-section">
          <div className="homio-container">
            <h2>HOMIO advice</h2>
          </div>
        </section>

        <section id="post-property" className="homio-section">
          <div className="homio-container">
            <h2>List a property with HOMIO</h2>
          </div>
        </section>
      </main>
    </>
  );
}
