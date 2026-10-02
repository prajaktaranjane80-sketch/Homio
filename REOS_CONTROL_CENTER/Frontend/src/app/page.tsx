import Link from "next/link";

import { AppShell } from "@/components/shell/AppShell";
import { Breadcrumbs } from "@/components/navigation/Breadcrumbs";
import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";

export default function HomePage() {
  return (
    <AppShell>
      <main id="main-content" className="page-shell">
        <div className="page-container">
          <Breadcrumbs
            items={[
              {
                label: "HOMIO",
                href: "/",
              },
            ]}
          />

          <section
            id="foundation"
            className="hero-section"
            aria-labelledby="hero-title"
          >
            <div className="hero-copy">
              <span className="eyebrow">GLOBAL REAL-ESTATE EXPERIENCE</span>

              <h1 id="hero-title">
                Global real estate.
                <span className="hero-highlight">
                  One clear journey.
                </span>
              </h1>

              <p className="hero-description">
                HOMIO turns the complexity of a global real-estate platform
                into a clear experience built around the way people actually
                discover, evaluate and move forward.
              </p>

              <div className="hero-actions">
                <Link className="button button--primary" href="#experience">
                  Explore the experience
                </Link>

                <Link className="button button--secondary" href="#boundary">
                  See how HOMIO works
                </Link>
              </div>
            </div>

            <aside className="hero-status" aria-label="HOMIO experience model">
              <Badge tone="success">HOMIO EXPERIENCE</Badge>

              <p>One continuous journey</p>

              <span>
                Discover ? Explore ? Decide ? Act ? Return
              </span>
            </aside>
          </section>

          <section
            id="experience"
            className="foundation-grid"
            aria-labelledby="experience-title"
          >
            <div className="sr-only">
              <h2 id="experience-title">The HOMIO experience</h2>
            </div>

            <Card>
              <span className="card-kicker">01 ? DISCOVER</span>
              <h2>Start from intent</h2>
              <p>
                The experience begins with what the user wants to achieve,
                rather than forcing them to understand platform structure.
              </p>
            </Card>

            <Card>
              <span className="card-kicker">02 ? EXPLORE</span>
              <h2>Understand what matters</h2>
              <p>
                Property, project, market and contextual information can grow
                deeper without changing the surrounding experience.
              </p>
            </Card>

            <Card>
              <span className="card-kicker">03 ? DECIDE</span>
              <h2>Keep the decision clear</h2>
              <p>
                Saving, comparison and return paths belong to the experience
                layer while authoritative business state remains elsewhere.
              </p>
            </Card>

            <Card>
              <span className="card-kicker">04 ? ACT</span>
              <h2>Move forward safely</h2>
              <p>
                Enquiry, visits and future transaction actions can enter the
                same journey without moving authority into the browser.
              </p>
            </Card>

            <Card>
              <span className="card-kicker">05 ? RETURN</span>
              <h2>Never lose the journey</h2>
              <p>
                HOMIO is designed so users can come back to context instead
                of rebuilding the same decision from the beginning.
              </p>
            </Card>
          </section>

          <section
            id="boundary"
            className="principles-section"
            aria-labelledby="boundary-title"
          >
            <div>
              <span className="eyebrow">PRODUCT BOUNDARY</span>
              <h2 id="boundary-title">
                Complexity stays behind the product.
              </h2>
            </div>

            <ul className="principles-list">
              <li>
                <strong>HOMIO owns the experience.</strong>
                <br />
                Navigation, presentation, interaction, loading, error and
                journey context stay inside the frontend boundary.
              </li>

              <li>
                <strong>REOS owns canonical business authority.</strong>
                <br />
                Inventory, identity, ownership, transactions, financial truth
                and other authoritative business capabilities remain outside
                the presentation layer.
              </li>

              <li>
                <strong>AI assists; it does not become authority.</strong>
                <br />
                Contextual intelligence can help explain, refine and guide
                without inventing facts or bypassing governed capabilities.
              </li>

              <li>
                <strong>ACRL remains an engineering-time boundary.</strong>
                <br />
                Continuity and recovery engineering do not become a runtime
                dependency of the production frontend.
              </li>

              <li>
                <strong>Every next feature plugs into the same foundation.</strong>
                <br />
                The shell, responsive behavior, accessibility patterns and
                shared primitives are established once and reused across F01?F13.
              </li>
            </ul>
          </section>

          <section className="principles-section" aria-labelledby="next-title">
            <div>
              <span className="eyebrow">FOUNDATION</span>
              <h2 id="next-title">
                Ready for verified discovery capabilities.
              </h2>
            </div>

            <div>
              <p className="hero-description">
                F01 establishes the production experience boundary. Future
                discovery capabilities can plug into this foundation without
                rebuilding the application shell or introducing a second
                business authority.
              </p>

              <div className="hero-actions">
                <Link className="button button--primary" href="#main-content">
                  Back to top
                </Link>
              </div>
            </div>
          </section>
        </div>
      </main>
    </AppShell>
  );
}