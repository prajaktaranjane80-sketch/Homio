import type { ReactNode } from "react";

import styles from "./PostProperty.module.css";

import type { PostPropertyStep } from "./post-property.types";

type Props = Readonly<{
  activeStep: PostPropertyStep;
  children: ReactNode;
  title?: string;
  description?: string;
}>;

const STEPS: readonly Readonly<{ id: PostPropertyStep; label: string }>[] = [
  { id: "type", label: "Type" },
  { id: "location", label: "Location" },
  { id: "ownership", label: "Ownership" },
  { id: "details", label: "Details" },
  { id: "media", label: "Media" },
  { id: "documents", label: "Documents" },
  { id: "pricing", label: "Pricing" },
  { id: "availability", label: "Availability" },
  { id: "review", label: "Review" },
  { id: "verification", label: "Verification" },
  { id: "submit", label: "Submit" },
  { id: "status", label: "Status" },
];

export default function PostPropertyShell({
  activeStep,
  children,
  title = "Bring your property to HOMIO",
  description = "Provide accurate property information. Submission, verification and publication are separate steps controlled by approved services.",
}: Props) {
  const activeIndex = STEPS.findIndex((step) => step.id === activeStep);

  return (
    <main className={styles.postPropertyRoot}>
      <header className={styles.postHeader}>
        <div>
          <span className={styles.postEyebrow}>HOMIO · PROPERTY SUBMISSION</span>
          <h1 className={styles.postTitle}>{title}</h1>
          <p className={styles.postDescription}>{description}</p>
        </div>
      </header>

      <nav className={styles.postProgress} aria-label="Property submission steps">
        {STEPS.map((step, index) => (
          <span
            key={step.id}
            className={`${styles.postStep} ${step.id === activeStep ? styles.postStepActive : ""}`}
            aria-current={step.id === activeStep ? "step" : undefined}
          >
            <span className={styles.postStepNumber}>
              {index < activeIndex ? "✓" : index + 1}
            </span>
            {step.label}
          </span>
        ))}
      </nav>

      {children}
    </main>
  );
}
