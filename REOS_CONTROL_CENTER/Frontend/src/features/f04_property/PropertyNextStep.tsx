import styles from "./PropertyNextStep.module.css";

export default function PropertyNextStep() {
  return (
    <section
      className={styles.section}
      id="property-next-step"
      aria-labelledby="property-next-step-heading"
    >
      <div className={styles.content}>
        <span className={styles.eyebrow}>
          NEXT STEP PREVIEW
        </span>

        <h2 id="property-next-step-heading">
          Ready to take the conversation forward?
        </h2>

        <p className={styles.lead}>
          Choose the path you want to explore. Lead creation,
          qualification, agent routing and visit scheduling are not
          connected on this experience preview.
        </p>

        <div className={styles.options}>
          <article
            id="property-next-step-enquiry"
            className={styles.option}
            aria-labelledby="property-enquiry-heading"
          >
            <span className={styles.optionLabel}>
              ENQUIRY
            </span>

            <h3 id="property-enquiry-heading">
              Ask about this property
            </h3>

            <p className={styles.optionDescription}>
              The enquiry capability will require an approved form,
              consent handling and a connected submission endpoint.
            </p>

            <button
              type="button"
              className={styles.primary}
              disabled
              aria-describedby="property-enquiry-disclosure"
            >
              Enquiry workflow not connected
            </button>

            <p
              id="property-enquiry-disclosure"
              className={styles.disclosure}
            >
              No request has been created or sent. This control remains
              disabled until the approved capability is connected.
            </p>
          </article>

          <article
            id="property-next-step-visit"
            className={styles.option}
            aria-labelledby="property-visit-heading"
          >
            <span className={styles.optionLabel}>
              VISIT
            </span>

            <h3 id="property-visit-heading">
              Plan a property visit
            </h3>

            <p className={styles.optionDescription}>
              Scheduling requires confirmed availability, the relevant
              contact workflow and an approved booking capability.
            </p>

            <button
              type="button"
              className={styles.primary}
              disabled
              aria-describedby="property-visit-disclosure"
            >
              Visit workflow not connected
            </button>

            <p
              id="property-visit-disclosure"
              className={styles.disclosure}
            >
              No request has been created or sent. A visit is not booked
              by viewing or sharing this page.
            </p>
          </article>
        </div>
      </div>
    </section>
  );
}
