import Link from "next/link";
import styles from "./RentalSection.module.css";

const rentals = [
  {
    title: "Furnished City Apartment",
    location: "Downtown Dubai",
    type: "2 Bed · Furnished",
    price: "AED 12,500 / month",
    href: "/property/furnished-city-apartment",
    image:
      "https://images.unsplash.com/photo-1600607688969-a5bfcd646154?auto=format&fit=crop&w=1400&q=85",
  },
  {
    title: "Marina Lifestyle Home",
    location: "Dubai Marina",
    type: "1 Bed · Furnished",
    price: "AED 8,500 / month",
    href: "/property/marina-lifestyle-home",
    image:
      "https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?auto=format&fit=crop&w=1400&q=85",
  },
  {
    title: "Central Singapore Residence",
    location: "Orchard, Singapore",
    type: "2 Bed · Long Term",
    price: "SGD 7,800 / month",
    href: "/property/central-singapore-residence",
    image:
      "https://images.unsplash.com/photo-1600607687920-4e2a09cf159d?auto=format&fit=crop&w=1400&q=85",
  },
];

export default function RentalSection() {
  return (
    <section className={styles.section}>
      <div className="homio-container">
        <div className={styles.header}>
          <div>
            <span className={styles.eyebrow}>RENT WITH HOMIO</span>

            <h2>Flexible homes for the next chapter.</h2>

            <p>
              Search furnished and long-term rental opportunities with the same
              clear property discovery experience.
            </p>
          </div>

          <Link
            href="/search?intent=rent"
            className={styles.viewAll}
          >
            Explore rentals
            <span aria-hidden="true">↗</span>
          </Link>
        </div>

        <div className={styles.content}>
          <div className={styles.feature}>
            <div className={styles.featureImage}>
              <img
                src={rentals[0].image}
                alt={rentals[0].title}
                loading="lazy"
              />

              <span className={styles.furnished}>Furnished</span>
            </div>

            <div className={styles.featureBody}>
              <span className={styles.type}>{rentals[0].type}</span>

              <Link href={rentals[0].href} className={styles.featureTitle}>
                {rentals[0].title}
              </Link>

              <p>{rentals[0].location}</p>

              <strong>{rentals[0].price}</strong>

              <Link href={rentals[0].href} className={styles.featureAction}>
                View rental
                <span aria-hidden="true">→</span>
              </Link>
            </div>
          </div>

          <div className={styles.list}>
            {rentals.slice(1).map((rental) => (
              <article key={rental.title} className={styles.card}>
                <Link href={rental.href} className={styles.cardImageLink}>
                  <div className={styles.cardImage}>
                    <img
                      src={rental.image}
                      alt={rental.title}
                      loading="lazy"
                    />
                  </div>
                </Link>

                <div className={styles.cardBody}>
                  <span className={styles.type}>{rental.type}</span>

                  <Link href={rental.href} className={styles.cardTitle}>
                    {rental.title}
                  </Link>

                  <p>{rental.location}</p>

                  <div className={styles.cardFooter}>
                    <strong>{rental.price}</strong>

                    <Link href={rental.href} className={styles.smallAction}>
                      View
                      <span aria-hidden="true">→</span>
                    </Link>
                  </div>
                </div>
              </article>
            ))}
          </div>
        </div>

        <div className={styles.rentalBar}>
          <div>
            <span className={styles.rentalLabel}>RENTING MADE CLEARER</span>
            <strong>
              Compare location, property type and rental context before you
              enquire.
            </strong>
          </div>

          <Link href="/search?intent=rent" className={styles.rentalAction}>
            Start rental search
          </Link>
        </div>
      </div>
    </section>
  );
}
