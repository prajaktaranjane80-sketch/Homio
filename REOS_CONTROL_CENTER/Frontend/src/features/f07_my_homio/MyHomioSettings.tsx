"use client";

import type { MyHomioProfile } from "./my-homio.types";

import {
  clearAllActivity,
  useMyHomioActivity,
} from "./myHomioActivityStore";

import styles from "./MyHomio.module.css";

type Props = Readonly<{
  profile: MyHomioProfile;
}>;

export default function MyHomioSettings({ profile }: Props) {
  const activity = useMyHomioActivity();

  const activityCount =
    activity.recentSearches.length +
    activity.savedSearches.length +
    activity.recentViews.length;

  function clearActivity() {
    if (
      typeof window !== "undefined" &&
      window.confirm(
        "Clear recent searches, saved requirements and recent-view history from this browser tab? F06 saved and comparison items will not be changed.",
      )
    ) {
      clearAllActivity();
    }
  }

  return (
    <>
      <header className={styles.panelHeader}>
        <p className={styles.kicker}>ACCOUNT PREFERENCES</p>

        <h2 className={styles.panelTitle}>Settings & privacy</h2>

        <p className={styles.panelLead}>
          Review account identity and the data currently held by this browser
          experience. A setting is only presented as active where it actually
          changes application behavior.
        </p>
      </header>

      <div className={styles.contentGrid}>
        <article className={styles.featureCard}>
          <div className={styles.featureHead}>
            <h3 className={styles.featureTitle}>Identity and sign-in</h3>
            <span className={styles.statusBadge}>Provider managed</span>
          </div>

          <p className={styles.featureText}>
            Signed in as {profile.email || profile.name || "HOMIO member"}.
            Email verification is{" "}
            {profile.emailVerified ? "confirmed by the identity provider" : "not confirmed"}.
            Password and identity security changes belong to the configured
            identity provider.
          </p>
        </article>

        <article className={styles.featureCard}>
          <div className={styles.featureHead}>
            <h3 className={styles.featureTitle}>Activity in this tab</h3>
            <span className={styles.statusBadge}>Session storage</span>
          </div>

          <p className={styles.featureText}>
            {activityCount} recent-search, saved-requirement and recently-viewed
            record(s) are currently held in this browser tab. This activity is
            not synchronized with your account.
          </p>

          <button
            type="button"
            className={`${styles.button} ${styles.buttonPrimary}`}
            style={{ marginTop: 14 }}
            disabled={activityCount === 0}
            onClick={clearActivity}
          >
            Clear browser activity
          </button>
        </article>

        <article className={styles.featureCard}>
          <h3 className={styles.featureTitle}>Saved items and comparison</h3>
          <p className={styles.featureText}>
            F06 Save and Compare use their existing in-memory store. They
            reset after a full page reload. Clearing activity above does not
            remove those selections.
          </p>
          <span className={styles.statusBadge}>F06 session only</span>
        </article>

        <article className={styles.featureCard}>
          <h3 className={styles.featureTitle}>Alerts and privacy controls</h3>
          <p className={styles.featureText}>
            Account-level alert preferences, data export, consent management
            and account deletion have no connected account API in this screen.
            No controls are presented as if those requests have been saved.
          </p>
          <span className={styles.statusBadge}>Integration required</span>
        </article>
      </div>

      <div className={styles.notice}>
        Clearing browser activity removes F07 recent searches, saved
        requirements and recent views only. It does not sign you out, delete
        account data on a server or clear the separate F06 Save/Compare store.
      </div>
    </>
  );
}
