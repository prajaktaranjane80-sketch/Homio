import Link from "next/link";

import { GlobalSearch } from "@/components/navigation/GlobalSearch";
import { Card } from "@/components/ui/Card";
import { AppShell } from "@/components/shell/AppShell";

const cityCards = [
  {
    name: "Mumbai",
    region: "Maharashtra",
    image:
      "https://images.unsplash.com/photo-1769556863948-f78da394a94e?auto=format&fit=crop&w=1400&q=82",
  },
  {
    name: "Pune",
    region: "Maharashtra",
    image:
      "https://images.unsplash.com/photo-1553064483-f10fe837615f?auto=format&fit=crop&w=1200&q=82",
  },
  {
    name: "Bengaluru",
    region: "Karnataka",
    image:
      "https://images.unsplash.com/photo-1782977697822-aa50585579a9?auto=format&fit=crop&w=1200&q=82",
  },
  {
    name: "Delhi NCR",
    region: "Delhi",
    image:
      "https://images.unsplash.com/photo-1657693221998-ffe0bf5cb424?auto=format&fit=crop&w=1200&q=82",
  },
];

const categories = [
  "Buy",
  "Rent",
  "Commercial",
  "New Projects",
];

export default function HomePage() {
  return (
    <AppShell>
      <main id="main-content" className="page-shell">
        <section className="home-hero" aria-labelledby="home-title">
          <div className="page-container home-hero__grid">
            <div className="home-hero__content">
              <span className="home-kicker">INDIA REAL ESTATE</span>

              <h1 id="home-title">
                Find a place that
                <span>fits your life.</span>
              </h1>

              <p>
                Search homes, rentals, commercial spaces and new projects
                across India ? in one simple place.
              </p>

              <div id="search" className="home-search">
                <div className="home-search__tabs" aria-label="Property intent">
                  {categories.map((category, index) => (
                    <span
                      className={
                        index === 0
                          ? "home-search__tab home-search__tab--active"
                          : "home-search__tab"
                      }
                      key={category}
                    >
                      {category}
                    </span>
                  ))}
                </div>

                <GlobalSearch />
              </div>

              <div className="home-quick-links" aria-label="Popular cities">
                <span>Popular cities</span>
                <a href="#cities">Mumbai</a>
                <a href="#cities">Pune</a>
                <a href="#cities">Bengaluru</a>
                <a href="#cities">Delhi NCR</a>
              </div>
            </div>

            <div className="home-hero__visual" aria-hidden="true">
              <div
                className="home-hero__image"
                style={{
                  backgroundImage:
                    "url('https://images.unsplash.com/photo-1769556863948-f78da394a94e?auto=format&fit=crop&w=1600&q=84')",
                }}
              />

              <div className="home-hero__visual-card">
                <span>HOMIO</span>
                <strong>Search less. Understand more.</strong>
              </div>
            </div>
          </div>
        </section>

        <section className="home-categories" aria-labelledby="category-title">
          <div className="page-container">
            <div className="section-heading">
              <div>
                <span className="section-kicker">START HERE</span>
                <h2 id="category-title">What are you looking for?</h2>
              </div>

              <p>
                Clear starting points for the most common property journeys.
              </p>
            </div>

            <div className="category-grid">
              <Link className="category-card category-card--active" href="#search">
                <span>01</span>
                <strong>Buy a home</strong>
                <small>Flats, houses and more</small>
              </Link>

              <Link className="category-card" href="#search">
                <span>02</span>
                <strong>Rent a home</strong>
                <small>Find a place that suits you</small>
              </Link>

              <Link className="category-card" href="#search">
                <span>03</span>
                <strong>Commercial</strong>
                <small>Office and business spaces</small>
              </Link>

              <Link className="category-card" href="#search">
                <span>04</span>
                <strong>New projects</strong>
                <small>Explore upcoming communities</small>
              </Link>
            </div>
          </div>
        </section>

        <section id="cities" className="home-cities" aria-labelledby="city-title">
          <div className="page-container">
            <div className="section-heading">
              <div>
                <span className="section-kicker">EXPLORE INDIA</span>
                <h2 id="city-title">Popular cities</h2>
              </div>

              <p>
                Start with a market you know. Your search journey stays simple
                as you go deeper.
              </p>
            </div>

            <div className="city-grid">
              {cityCards.map((city) => (
                <Link
                  href="#search"
                  className="city-card"
                  key={city.name}
                  aria-label={`Explore ${city.name} real estate`}
                >
                  <div
                    className="city-card__image"
                    style={{
                      backgroundImage: `url('${city.image}')`,
                    }}
                  />
                  <div className="city-card__overlay" />
                  <div className="city-card__content">
                    <span>{city.region}</span>
                    <strong>{city.name}</strong>
                  </div>
                </Link>
              ))}
            </div>
          </div>
        </section>

        <section className="home-simple" aria-labelledby="simple-title">
          <div className="page-container">
            <Card className="simple-card">
              <div>
                <span className="section-kicker">THE HOMIO APPROACH</span>
                <h2 id="simple-title">Real estate should feel simple.</h2>
              </div>

              <div className="simple-steps">
                <div>
                  <strong>Search</strong>
                  <span>Tell HOMIO what you need.</span>
                </div>

                <div>
                  <strong>Explore</strong>
                  <span>Understand the options.</span>
                </div>

                <div>
                  <strong>Decide</strong>
                  <span>Save and compare what matters.</span>
                </div>

                <div>
                  <strong>Move forward</strong>
                  <span>Take the next approved action.</span>
                </div>
              </div>
            </Card>
          </div>
        </section>

        <footer className="home-footer">
          <div className="page-container">
            <div className="home-footer__main">
              <div>
                <strong>HOMIO</strong>
                <p>
                  A simple India-first real-estate experience powered by REOS.
                </p>
              </div>

              <nav aria-label="Footer navigation">
                <a href="#search">Search</a>
                <a href="#cities">Cities</a>
                <a href="#category-title">Explore</a>
              </nav>
            </div>

            <div className="home-footer__bottom">
              <span>? HOMIO</span>
              <span>Experience layer powered by REOS</span>
            </div>
          </div>
        </footer>
      </main>
    </AppShell>
  );
}