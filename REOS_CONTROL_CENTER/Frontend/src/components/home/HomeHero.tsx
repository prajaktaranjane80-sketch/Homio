import { HomeIntentTabs } from "@/components/home/HomeIntentTabs";
import { HomeSearch } from "@/components/home/HomeSearch";

export function HomeHero() {
  return (
    <section className="home-hero-new" aria-labelledby="home-title">
      <div className="page-container">
        <div className="home-hero-new__grid">
          <div className="home-hero-new__copy">
            <span className="home-eyebrow">
              HOMIO · INDIA REAL ESTATE
            </span>

            <h1 id="home-title">
              Find the right property.
              <span>Move forward with HOMIO.</span>
            </h1>

            <p>
              Search homes, rentals, new projects and commercial spaces in one
              simple place. When you are ready, HOMIO helps you take the next
              approved step.
            </p>

            <div className="home-hero-new__trust">
              <span>Search</span>
              <span>Explore</span>
              <span>Compare</span>
              <span>Connect with HOMIO</span>
            </div>
          </div>

          <div className="home-hero-new__visual" aria-hidden="true">
            <div className="home-hero-new__city-card home-hero-new__city-card--large">
              <span>PUNE</span>
              <strong>Homes that fit your search.</strong>
            </div>

            <div className="home-hero-new__city-card home-hero-new__city-card--small top">
              <span>MUMBAI</span>
              <strong>Buy · Rent · Explore</strong>
            </div>

            <div className="home-hero-new__city-card home-hero-new__city-card--small bottom">
              <span>BENGALURU</span>
              <strong>Projects · Localities</strong>
            </div>

            <div className="home-hero-new__shape home-hero-new__shape--one" />
            <div className="home-hero-new__shape home-hero-new__shape--two" />
          </div>
        </div>

        <div className="home-hero-new__search">
          <HomeIntentTabs />
          <HomeSearch />
        </div>
      </div>
    </section>
  );
}
