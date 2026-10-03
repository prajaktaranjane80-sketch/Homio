import HomeHeader from "@/components/home/HomeHeader";
import HomeSecondaryNav from "@/components/home/HomeSecondaryNav";
import HomeHero from "@/components/home/HomeHero";
import HomeQuickDiscovery from "@/components/home/HomeQuickDiscovery";
import PopularCities from "@/components/home/PopularCities";
import PopularLocalities from "@/components/home/PopularLocalities";
import FeaturedProjects from "@/components/home/FeaturedProjects";
import NewProjectCollections from "@/components/home/NewProjectCollections";
import FreshProperties from "@/components/home/FreshProperties";

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

        <section id="commercial" className="homio-section">
          <div className="homio-container">
            <h2>Commercial real estate</h2>
          </div>
        </section>

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
