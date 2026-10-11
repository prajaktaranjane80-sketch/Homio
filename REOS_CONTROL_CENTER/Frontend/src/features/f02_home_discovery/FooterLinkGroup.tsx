import Link from "next/link";
import styles from "./FooterLinkGroup.module.css";

export type FooterLink = {
  label: string;
  href: string;
};

type Props = {
  title: string;
  links: FooterLink[];
};

export default function FooterLinkGroup({ title, links }: Props) {
  return (
    <div className={styles.column}>
      <h3>{title}</h3>

      {links.map((link) => (
        <Link key={link.label} href={link.href}>
          {link.label}
        </Link>
      ))}
    </div>
  );
}
