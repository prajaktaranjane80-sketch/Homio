import Link from "next/link";
import styles from "./HomeServices.module.css";

const services = [
  {
    title: "Home Loans",
    description:
      "Explore financing pathways and understand your estimated affordability.",
    href: "/services/home-loans",
    icon: "01",
  },
  {
    title: "Property Valuation",
    description:
      "Build a starting view of value using location and property context.",
    href: "/services/property-valuation",
    icon: "02",
  },
  {
    title: "Interiors",
    description:
      "Plan furniture, renovation and interior budgets around the property.",
    href: "/services/interiors",
    icon: "03",
  },
  {
    title: "Moving & Relocation",
    description:
      "Useful support around preparing for a move into a new home or city.",
    href: "/services/relocation",
    icon: "04",
  },
  {
    title: "Property Management",
    description:
      "Explore support options for ongoing ownership and rental needs.",
    href: "/services/property-management",
    icon: "05",
  },
  {
    title: "Expert Support",
    description:
      "Connect your property journey with the right HOMIO next step.",
    href: "/services/expert-support",
    icon: "06",
  },
];

export default function HomeServices() {
  return (
    <section id="services" className={styles.section}>
      <div className="homio-container">
        <div className={styles.header}>
          <div>
            <span className={styles.eyebrow}>HOMIO SERVICES</span>

            <h2>More than property discovery.</h2>

            <p>
              Helpful services around the property journey, presented as part
              of the same HOMIO experience.
            </p>
          </div>

          <Link href="/services" className={styles.viewAll}>
            Explore all services
            <span aria-hidden="true">↗</span>
          </Link>
        </div>

        <div className={styles.grid}>
          {services.map((service) => (
            <Link key={service.title} href={service.href} className={styles.card}>
              <div className={styles.top}>
                <span className={styles.number}>{service.icon}</span>

                <span className={styles.arrow} aria-hidden="true">
                  ↗
                </span>
              </div>

              <h3>{service.title}</h3>

              <p>{service.description}</p>

              <span className={styles.explore}>
                Explore service
                <span aria-hidden="true">→</span>
              </span>
            </Link>
          ))}
        </div>

        <div className={styles.bottom}>
          <div className={styles.bottomIcon} aria-hidden="true">
            H
          </div>

          <div>
            <strong>One property journey, connected end to end.</strong>

            <p>
              Discovery, research, services and brokerage should feel like one
              experience—not separate destinations.
            </p>
          </div>

          <Link href="/services" className={styles.bottomAction}>
            Explore HOMIO services
          </Link>
        </div>
      </div>
    </section>
  );
}
