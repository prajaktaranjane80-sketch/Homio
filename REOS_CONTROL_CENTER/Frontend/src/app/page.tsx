import Link from "next/link";

import { AppShell } from "@/components/shell/AppShell";
import { Breadcrumbs } from "@/components/navigation/Breadcrumbs";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";

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

          <section id="foundation" className="hero-section">
            <div className="hero-copy">
              <span className="eyebrow">GLOBAL REAL-ESTATE SAAS</span>

              <h1>
                The complexity stays behind the product.
                <span className="hero-highlight">
                  The experience stays clear.
                </span>
              </h1>

              <p className="hero-description">
                HOMIO transforms verified REOS capabilities into a simple,
                responsive and continuous real-estate experience.
              </p>

              <div className="hero-actions">
                <Link className="button button--primary" href="#foundation-grid">
                  Explore foundation
                </Link>

                <Link className="button button--secondary" href="#principles">
                  View principles
                </Link>
              </div>
            </div>

            <div className="hero-status">
              <Badge tone="success">F01 ACTIVE</Badge>
              <p>Production experience foundation.</p>
              <span>REOS-backed architecture boundary</span>
            </div>
          </section>

          <section id="foundation-grid" className="foundation-grid">
            <Card>
              <span className="card-kicker">SHELL</span>
              <h2>One coherent application frame</h2>
              <p>
                Navigation, context, responsive behavior and global actions
                share one foundation instead of being rebuilt inside features.
              </p>
            </Card>

            <Card>
              <span className="card-kicker">REUSE</span>
              <h2>One module, one responsibility</h2>
              <p>
                Each behavioral module has its own file. Feature modules
                consume the shared layer rather than creating competing UI
                systems.
              </p>
            </Card>

            <Card>
              <span className="card-kicker">BOUNDARY</span>
              <h2>Frontend is not business authority</h2>
              <p>
                The foundation owns presentation and interaction only.
                Canonical business truth remains inside REOS.
              </p>
            </Card>
          </section>

          <section id="principles" className="principles-section">
            <div>
              <span className="eyebrow">F01 FOUNDATION PRINCIPLES</span>
              <h2>Built to scale across F01–F13.</h2>
            </div>

            <ul className="principles-list">
              <li>No frontend duplicate business engines.</li>
              <li>No ACRL runtime dependency.</li>
              <li>No canonical business truth in browser state.</li>
              <li>Responsive behavior is intentional.</li>
              <li>Accessibility is part of every module.</li>
              <li>Production routes evolve without rewriting the shell.</li>
            </ul>
          </section>
        </div>
      </main>
    </AppShell>
  );
}
