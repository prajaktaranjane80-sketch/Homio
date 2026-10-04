import Link from "next/link";
import FooterLinkGroup, {
  type FooterLink,
} from "./FooterLinkGroup";
import FooterRegions from "./FooterRegions";
import FooterLegal from "./FooterLegal";
import styles from "./HomeFooter.module.css";

const exploreLinks: FooterLink[] = [
  { label: "Buy", href: "/search?intent=buy" },
  { label: "Rent", href: "/search?intent=rent" },
  { label: "Projects", href: "/search?intent=projects" },
  { label: "Commercial", href: "/search?intent=commercial" },
  { label: "Plots & Land", href: "/search?intent=land" },
];

const marketLinks: FooterLink[] = [
  { label: "Dubai", href: "/market/dubai" },
  { label: "Singapore", href: "/market/singapore" },
  { label: "Tokyo", href: "/market/tokyo" },
  { label: "London", href: "/market/london" },
  { label: "New York", href: "/market/new-york" },
];

const companyLinks: FooterLink[] = [
  { label: "About HOMIO", href: "/about" },
  { label: "HOMIO AI", href: "/ai" },
  { label: "Advice", href: "/advice" },
  { label: "Help Center", href: "/help" },
  { label: "Contact", href: "/help/contact" },
];

const professionalLinks: FooterLink[] = [
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
            <FooterLinkGroup title="Explore" links={exploreLinks} />
            <FooterLinkGroup title="Markets" links={marketLinks} />
            <FooterLinkGroup title="HOMIO" links={companyLinks} />
            <FooterLinkGroup
              title="For Professionals"
              links={professionalLinks}
            />
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

          <FooterRegions />
        </div>

        <FooterLegal />
      </div>
    </footer>
  );
}
