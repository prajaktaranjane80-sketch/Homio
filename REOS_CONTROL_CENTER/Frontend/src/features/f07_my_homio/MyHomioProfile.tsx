import type { MyHomioProfile as ProfileData } from "./my-homio.types";

import styles from "./MyHomio.module.css";

type Props = Readonly<{
  profile: ProfileData;
}>;

export default function MyHomioProfile({ profile }: Props) {
  const rows = [
    {
      label: "Display name",
      value: profile.name?.trim() || "Not supplied by identity provider",
    },
    {
      label: "Email address",
      value: profile.email?.trim() || "Not supplied by identity provider",
    },
    {
      label: "Email verification",
      value: profile.emailVerified
        ? "Verified by the identity provider"
        : "Not confirmed by the identity provider",
    },
    {
      label: "Account session",
      value: "Authenticated HOMIO session",
    },
  ];

  return (
    <>
      <header className={styles.panelHeader}>
        <p className={styles.kicker}>IDENTITY & ACCOUNT</p>

        <h2 className={styles.panelTitle}>Your profile</h2>

        <p className={styles.panelLead}>
          This profile view displays the identity claims supplied to the
          authenticated HOMIO session. It does not invent account details
          or pretend profile edits have been saved.
        </p>
      </header>

      <div className={styles.profileGrid}>
        {rows.map((row) => (
          <div className={styles.profileField} key={row.label}>
            <span className={styles.profileLabel}>{row.label}</span>
            <strong className={styles.profileValue}>{row.value}</strong>
          </div>
        ))}
      </div>

      <div className={styles.sectionHeading}>
        <div>
          <h3>Profile management</h3>
          <p>
            Changes to identity information must be performed by the
            configured identity provider until an approved profile API exists.
          </p>
        </div>
      </div>

      <div className={styles.featureCard}>
        <h3 className={styles.featureTitle}>Identity-provider managed</h3>
        <p className={styles.featureText}>
          Password changes, email updates, multifactor authentication and
          identity recovery are not handled by this read-only profile panel.
          The current screen does not submit or save any profile changes.
        </p>
        <span className={styles.statusBadge}>Read-only profile claims</span>
      </div>
    </>
  );
}
