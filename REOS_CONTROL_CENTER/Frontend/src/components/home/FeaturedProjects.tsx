"use client";

import Link from "next/link";

import styles from "./FeaturedProjects.module.css";

const projects = [
  {
    name: "Harbour Residences",
    location: "Dubai Harbour",
    category: "Luxury Residences",
    price: "Preview only",
    status: "Experience preview",
    href: "/project/harbour-residences",
    image:
      "https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?auto=format&fit=crop&w=1400&q=85",
  },
  {
    name: "Marina Crest",
    location: "Dubai Marina",
    category: "Waterfront Apartments",
    price: "Preview only",
    status: "Experience preview",
    href: "/project/marina-crest",
    image:
      "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?auto=format&fit=crop&w=1400&q=85",
  },
  {
    name: "The Meridian",
    location: "Singapore",
    category: "Urban Residences",
    price: "Preview only",
    status: "Experience preview",
    href: "/project/the-meridian",
    image:
      "https://images.unsplash.com/photo-1600607687920-4e2a09cf159d?auto=format&fit=crop&w=1400&q=85",
  },
];

export default function FeaturedProjects() {
  return (
    <section id="projects" className={styles.section}>
      <div className="homio-container">
        <div className={styles.header}>
          <div>
            <span className={styles.eyebrow}>FEATURED PROJECTS</span>

            <h2>Projects worth discovering.</h2>

            <p>
              Explore global project-experience previews. Pricing,
              availability and project facts are not verified inventory.
            </p>
          </div>

          <Link href="/search?intent=projects" className={styles.viewAll}>
            View all projects
            <span aria-hidden="true">↗</span>
          </Link>
        </div>

        <div className={styles.grid}>
          {projects.map((project) => (
            <Link
              key={project.name}
              href={project.href}
              className={styles.card}
            >
              <div className={styles.imageWrap}>
                <img
                  src={project.image}
                  alt={`${project.name} experience preview`}
                  className={styles.image}
                  loading="lazy"
                />

                <span className={styles.status}>{project.status}</span>
              </div>

              <div className={styles.body}>
                <span className={styles.category}>{project.category}</span>

                <h3>{project.name}</h3>

                <p className={styles.location}>{project.location}</p>

                <div className={styles.footer}>
                  <span>{project.price}</span>

                  <span className={styles.details}>
                    Explore <span aria-hidden="true">→</span>
                  </span>
                </div>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </section>
  );
}
