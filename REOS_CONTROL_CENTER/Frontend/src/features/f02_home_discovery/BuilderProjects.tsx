import Link from "next/link";
import styles from "./BuilderProjects.module.css";

const builders = [
  {
    name: "Atlas Developments",
    focus: "Dubai · Luxury residential",
    label: "Example profile",
    href: "/search?intent=projects",
    image:
      "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?auto=format&fit=crop&w=1000&q=85",
  },
  {
    name: "Meridian Living",
    focus: "Singapore · Urban residences",
    label: "Example profile",
    href: "/search?intent=projects",
    image:
      "https://images.unsplash.com/photo-1487958449943-2429e8be8625?auto=format&fit=crop&w=1000&q=85",
  },
  {
    name: "Northstar Properties",
    focus: "London · Prime residential",
    label: "Example profile",
    href: "/search?intent=projects",
    image:
      "https://images.unsplash.com/photo-1460317442991-0ec209397118?auto=format&fit=crop&w=1000&q=85",
  },
];

const signals = [
  "Project and configuration context",
  "Location and market context",
  "A connected property-to-project journey",
  "Clear next steps when supported",
];

export default function BuilderProjects() {
  return (
    <section className={styles.section}>
      <div className="homio-container">
        <div className={styles.header}>
          <div>
            <span className={styles.eyebrow}>BUILDER PROJECTS</span>

            <h2>Discover developments through their portfolios.</h2>

            <p>
              Example developer profiles demonstrate how project
              discovery can be organized inside HOMIO. These profiles
              are illustrative; they are not verified builder accounts
              or confirmed live inventory.
            </p>
          </div>

          <Link href="/search?intent=projects" className={styles.viewAll}>
            Explore project discovery
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
                  
              <Image
              src={builder.image}
              width={1000}
              height={750}
              sizes="(max-width: 640px) 100vw, (max-width: 900px) 50vw, 33vw"
              alt={`Illustrative architecture image for ${builder.name}`}
              className={styles.image}
              loading="lazy"
              />


                  <span className={styles.projectCount}>
                    {builder.label}
                  </span>
                </div>

                <div className={styles.body}>
                  <span className={styles.label}>
                    ILLUSTRATIVE PROFILE
                  </span>

                  <h3>{builder.name}</h3>

                  <p>{builder.focus}</p>

                  <span className={styles.explore}>
                    Explore project previews
                    <span aria-hidden="true">→</span>
                  </span>
                </div>
              </Link>
            ))}
          </div>

          <aside className={styles.sidePanel}>
            <span className={styles.panelEyebrow}>PROJECT DISCOVERY</span>

            <h3>Evaluate a development with more context.</h3>

            <p>
              The intended journey connects a project with its
              configurations, location context and relevant property
              details. Actual availability must be confirmed by an
              authoritative source.
            </p>

            <div className={styles.signals}>
              {signals.map((signal) => (
                <div key={signal} className={styles.signal}>
                  <span className={styles.check} aria-hidden="true">
                    →
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
            <span className={styles.bottomLabel}>
              FOR BUILDERS & DEVELOPERS
            </span>

            <strong>
              Explore how developer portfolios can connect to HOMIO
              project discovery and brokerage journeys.
            </strong>
          </div>

          <Link
            href="/search?intent=projects"
            className={styles.bottomAction}
          >
            Explore project discovery
          </Link>
        </div>
      </div>
    </section>
  );
}
