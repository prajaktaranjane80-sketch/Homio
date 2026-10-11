import Link from "next/link";
import styles from "./PopularCities.module.css";

const cities = [
  {
    name: "Dubai",
    country: "United Arab Emirates",
    market: "Luxury, residential & investment",
    href: "/search?city=dubai",
    image:
      "https://images.unsplash.com/photo-1512453979798-5ea266f8880c?auto=format&fit=crop&w=1200&q=85",
  },
  {
    name: "Singapore",
    country: "Singapore",
    market: "Residential, commercial & investment",
    href: "/search?city=singapore",
    image:
      "https://images.unsplash.com/photo-1525625293386-3f8f99389edd?auto=format&fit=crop&w=1200&q=85",
  },
  {
    name: "Tokyo",
    country: "Japan",
    market: "Urban homes & investment",
    href: "/search?city=tokyo",
    image:
      "https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?auto=format&fit=crop&w=1200&q=85",
  },
  {
    name: "London",
    country: "United Kingdom",
    market: "Prime residential & commercial",
    href: "/search?city=london",
    image:
      "https://images.unsplash.com/photo-1513635269975-59663e0ac1ad?auto=format&fit=crop&w=1200&q=85",
  },
  {
    name: "New York",
    country: "United States",
    market: "Residential, commercial & luxury",
    href: "/search?city=new-york",
    image:
      "https://images.unsplash.com/photo-1522083165195-3424ed129620?auto=format&fit=crop&w=1200&q=85",
  },
];

export default function PopularCities() {
  return (
    <section id="locations" className={styles.section}>
      <div className="homio-container">
        <div className={styles.heading}>
          <div>
            <span className={styles.eyebrow}>GLOBAL DESTINATIONS</span>

            <h2>Explore leading real estate cities.</h2>
          </div>

          <p>
            Discover residential, commercial, luxury and investment
            opportunities across markets connected to the HOMIO brokerage
            experience.
          </p>
        </div>

        <div className={styles.grid}>
          {cities.map((city) => (
            <Link
              key={city.name}
              href={city.href}
              className={styles.card}
              style={{ backgroundImage: `url("${city.image}")` }}
            >
              <span className={styles.overlay} />

              <div className={styles.content}>
                <span className={styles.country}>{city.country}</span>

                <h3>{city.name}</h3>

                <p>{city.market}</p>

                <span className={styles.explore}>
                  Explore market <span aria-hidden="true">↗</span>
                </span>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </section>
  );
}
