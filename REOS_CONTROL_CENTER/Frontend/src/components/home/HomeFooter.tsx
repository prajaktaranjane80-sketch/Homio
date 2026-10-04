import Link from "next/link";
import styles from "./HomeFooter.module.css";

const exploreLinks = [
  { label: "Buy", href: "/search?intent=buy" },
  { label: "Rent", href: "/search?intent=rent" },
  { label: "Projects", href: "/search?intent=projects" },
  { label: "Commercial", href: "/search?intent=commercial" },
  { label: "Plots & Land", href: "/search?intent=land" },
];

const marketLinks = [
  { label: "Dubai", href: "/market/dubai" },
  { label: "Singapore", href: "/market/singapore" },
  { label: "Tokyo", href: "/market/tokyo" },
  { label: "London", href: "/market/london" },
  { label: "New York", href: "/market/new-york" },
];

const companyLinks = [
  { label: "About HOMIO", href: "/about" },
  { label: "HOMIO AI", href: "/ai" },
  { label: "Advice", href: "/advice" },
  { label: "Help Center", href: "/help" },
  { label: "Contact", href: "/help/contact" },
];

const professionalLinks = [
  { label: "HOMIO Pro", href: "/pro" },
  { label: "Inventory", href: "/pro/inventory" },
  { label: "Leads", href: "/pro/leads" },
  { label: "Deals", href: "/pro/deals" },
];

export default function HomeFooter() {
  return (
    <footer className={styles.footer}>
      <div className="homio-container">
        <div className={styles.top}>
          <div className={styles.brandColumn}>
            <Link href="/" className={styles.logo} aria-label="HOMIO home">
              <span className={styles.logoMark}>H</span>
              <span className={styles.logoText}>HOMIO</span>
            </Link>

            <p>
              Global real estate discovery, intelligence and brokerage in one
              connected experience.
            </p>

            <Link href="/search" className={styles.cta}>
              Start your property journey
              <span aria-hidden="true">↗</span>
            </Link>
          </div>

          <div className={styles.columns}>
            <div className={styles.column}>
              <h3>Explore</h3>

              {exploreLinks.map((link) => (
                <Link key={link.label} href={link.href}>
                  {link.label}
                </Link>
              ))}
            </div>

            <div className={styles.column}>
              <h3>Markets</h3>

              {marketLinks.map((link) => (
                <Link key={link.label} href={link.href}>
                  {link.label}
                </Link>
              ))}
            </div>

            <div className={styles.column}>
              <h3>HOMIO</h3>

              {companyLinks.map((link) => (
                <Link key={link.label} href={link.href}>
                  {link.label}
                </Link>
              ))}
            </div>

            <div className={styles.column}>
              <h3>For Professionals</h3>

              {professionalLinks.map((link) => (
                <Link key={link.label} href={link.href}>
                  {link.label}
                </Link>
              ))}
            </div>
          </div>
        </div>

        <div className={styles.middle}>
          <div>
            <span className={styles.middleLabel}>GLOBAL EXPERIENCE</span>

            <strong>
              Designed for modern residential, commercial and investment
              journeys.
            </strong>
          </div>

          <div className={styles.regions}>
            <span>Americas</span>
            <span>Europe</span>
            <span>Middle East</span>
            <span>Asia Pacific</span>
          </div>
        </div>

        <div className={styles.bottom}>
          <span>
            © {new Date().getFullYear()} HOMIO. All rights reserved.
          </span>

          <div className={styles.legal}>
            <Link href="/privacy">Privacy</Link>
            <Link href="/terms">Terms</Link>
            <Link href="/cookies">Cookies</Link>
            <Link href="/accessibility">Accessibility</Link>
          </div>

          <div className={styles.social}>
            <Link href="/social" aria-label="HOMIO social channels">
              Social
            </Link>
          </div>
        </div>
      </div>
    </footer>
  );
}
