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
  { label: "Dubai", href: "/search?city=Dubai" },
  { label: "Singapore", href: "/search?city=Singapore" },
  { label: "Tokyo", href: "/search?city=Tokyo" },
  { label: "London", href: "/search?city=London" },
  { label: "New York", href: "/search?city=New%20York" },
];

const companyLinks: FooterLink[] = [
  { label: "About HOMIO", href: "/#why-homio" },
  { label: "HOMIO AI preview", href: "/#homio-ai" },
  { label: "Advice previews", href: "/#advice" },
  { label: "Help & Support", href: "/#help" },
  { label: "Trust approach", href: "/#trust" },
];

const professionalLinks: FooterLink[] = [
  { label: "List with HOMIO", href: "/#post-property" },
  { label: "Project previews", href: "/#projects" },
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
