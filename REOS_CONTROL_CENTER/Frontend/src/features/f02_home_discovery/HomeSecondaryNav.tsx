import Link from "next/link";
import styles from "./HomeSecondaryNav.module.css";

const links = [
  { label: "Explore", href: "#explore" },
  { label: "Locations", href: "#locations" },
  { label: "Projects", href: "#projects" },
  { label: "Commercial", href: "#commercial" },
  { label: "Tools", href: "#tools" },
  { label: "Advice", href: "#advice" },
];

export default function HomeSecondaryNav() {
  return (
    <nav className={styles.bar} aria-label="HOMIO discovery navigation">
      <div className={`homio-container ${styles.inner}`}>
        {links.map((link) => (
          <Link key={link.href} href={link.href} className={styles.link}>
            {link.label}
          </Link>
        ))}

        <Link href="#post-property" className={styles.postLink}>
          List a Property
        </Link>
      </div>
    </nav>
  );
}
