import Link from "next/link";
import styles from "./BuilderProjects.module.css";

const builders = [
  {
    name: "Atlas Developments",
    focus: "Dubai · Luxury residential",
    projects: "12 active projects",
    href: "/search?builder=atlas-developments",
    image:
      "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?auto=format&fit=crop&w=1000&q=85",
  },
  {
    name: "Meridian Living",
    focus: "Singapore · Urban residences",
    projects: "8 active projects",
    href: "/search?builder=meridian-living",
    image:
      "https://images.unsplash.com/photo-1487958449943-2429e8be8625?auto=format&fit=crop&w=1000&q=85",
  },
  {
    name: "Northstar Properties",
    focus: "London · Prime residential",
    projects: "6 active projects",
    href: "/search?builder=northstar-properties",
    image:
      "https://images.unsplash.com/photo-1460317442991-0ec209397118?auto=format&fit=crop&w=1000&q=85",
  },
];

const signals = [
  "Project portfolio context",
  "Configuration and availability",
  "Location and market context",
  "Direct HOMIO project journey",
];

export default function BuilderProjects() {
  return (
    <section className={styles.section}>
      <div className="homio-container">
        <div className={styles.header}>
          <div>
            <span className={styles.eyebrow}>BUILDER PROJECTS</span>

            <h2>Discover projects by the people building them.</h2>

            <p>
              Explore project portfolios and individual developments while
              keeping the consumer journey centered on HOMIO—not a competing
              broker marketplace.
            </p>
          </div>

          <Link href="/search?intent=projects" className={styles.viewAll}>
            Explore projects
            <span aria-hidden="true">↗</span>
          </Link>
        </div>

        <div className={styles.layout}>
          <div className={styles.builderGrid}>
            {builders.map((builder) => (
              <Link
                key={builder.name}
                href={builder.href}
                className={styles.card}
              >
                <div className={styles.imageWrap}>
                  <img
                    src={builder.image}
                    alt={builder.name}
                    className={styles.image}
                    loading="lazy"
                  />

                  <span className={styles.projectCount}>
                    {builder.projects}
                  </span>
                </div>

                <div className={styles.body}>
                  <span className={styles.label}>BUILDER PROFILE</span>

                  <h3>{builder.name}</h3>

                  <p>{builder.focus}</p>

                  <span className={styles.explore}>
                    View projects
                    <span aria-hidden="true">→</span>
                  </span>
                </div>
              </Link>
            ))}
          </div>

          <aside className={styles.sidePanel}>
            <span className={styles.panelEyebrow}>PROJECT DISCOVERY</span>

            <h3>A better way to evaluate new development.</h3>

            <p>
              Start from the project, then move through configurations,
              availability, location and the next HOMIO brokerage action.
            </p>

            <div className={styles.signals}>
              {signals.map((signal) => (
                <div key={signal} className={styles.signal}>
                  <span className={styles.check} aria-hidden="true">
                    ✓
                  </span>
                  <span>{signal}</span>
                </div>
              ))}
            </div>

            <Link
              href="/search?intent=projects"
              className={styles.panelAction}
            >
              Start project discovery
              <span aria-hidden="true">↗</span>
            </Link>
          </aside>
        </div>

        <div className={styles.bottom}>
          <div>
            <span className={styles.bottomLabel}>FOR BUILDERS & DEVELOPERS</span>

            <strong>
              Bring your project inventory into a structured HOMIO discovery
              and brokerage journey.
            </strong>
          </div>

          <Link href="/pro/inventory" className={styles.bottomAction}>
            Explore partner pathway
          </Link>
        </div>
      </div>
    </section>
  );
}
