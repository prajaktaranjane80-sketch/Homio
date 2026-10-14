"use client";

import { useSaveCompareSession } from "@/features/f06_save_compare/saveCompareSession";

import { useMyHomioActivity } from "./myHomioActivityStore";

import type {
  MyHomioProfile,
  MyHomioSection,
} from "./my-homio.types";

import styles from "./MyHomio.module.css";

type Props = Readonly<{
  profile: MyHomioProfile;
  onNavigate: (section: MyHomioSection) => void;
}>;

function formatActivityDate(value: string): string {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "Time not supplied";
  }

  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(date);
}

export default function MyHomioDashboard({
  profile,
  onNavigate,
}: Props) {
  const { savedRecords, comparedItems } = useSaveCompareSession();
  const activity = useMyHomioActivity();

  const featuredSaved = savedRecords.slice(0, 3);
  const featuredSearches = activity.recentSearches.slice(0, 3);
  const featuredViews = activity.recentViews.slice(0, 3);

  const nextAction =
    savedRecords.length === 0
      ? {
          eyebrow: "BUILD YOUR SHORTLIST",
          title: "Save the properties and projects worth another look.",
          text: "Your shortlist updates when you use Save in search or on a detail page.",
          label: "Explore HOMIO",
          href: "/search",
        }
      : comparedItems.length < 2
        ? {
            eyebrow: "MAKE A MORE INFORMED DECISION",
            title: "Compare the options already on your shortlist.",
            text: "View the supplied facts side by side. Missing information stays visible.",
            label: "Open comparison",
            href: "/compare",
          }
        : {
            eyebrow: "CONTINUE YOUR DECISION",
            title: "Your comparison is ready to review.",
            text: "Return to the current board and check details before deciding what to explore next.",
            label: "Review comparison",
            href: "/compare",
          };

  return (
    <>
      <div className={styles.featureCard}>
        <div className={styles.featureHead}>
          <div>
            <p className={styles.kicker}>YOUR NEXT STEP</p>
            <h3 className={styles.featureTitle}>{nextAction.title}</h3>
          </div>
          <span className={styles.statusBadge}>Personal workspace</span>
        </div>

        <p className={styles.featureText}>{nextAction.text}</p>

        <div className={styles.panelActions}>
          <a
            className={`${styles.button} ${styles.buttonPrimary}`}
            href={nextAction.href}
          >
            {nextAction.label} <span aria-hidden="true">↗</span>
          </a>

          <button
            type="button"
            className={styles.button}
            onClick={() => onNavigate("recent-searches")}
          >
            Reopen a search
          </button>
        </div>
      </div>

      <div className={styles.sectionHeading}>
        <div>
          <h3>Your recent activity</h3>
          <p>
            Activity comes from this browser tab. It is not represented as
            account-synced history.
          </p>
        </div>

        <button
          type="button"
          className={styles.textLink}
          onClick={() => onNavigate("recent-searches")}
        >
          View activity →
        </button>
      </div>

      <div className={styles.contentGrid}>
        <section className={styles.featureCard} aria-labelledby="dashboard-searches">
          <div className={styles.featureHead}>
            <h3 id="dashboard-searches" className={styles.featureTitle}>
              Recent searches
            </h3>
            <span className={styles.navCount}>
              {activity.recentSearches.length}
            </span>
          </div>

          {featuredSearches.length === 0 ? (
            <p className={styles.featureText}>
              Your real search activity will appear here after you explore
              HOMIO and change search criteria.
            </p>
          ) : (
            <div className={styles.activityList} style={{ marginTop: 13 }}>
              {featuredSearches.map((search) => (
                <article className={styles.activityRow} key={search.id}>
                  <div className={styles.activityMain}>
                    <a className={styles.activityTitle} href={search.href}>
                      {search.title}
                    </a>
                    <span className={styles.activityMeta}>
                      {[search.location, search.filtersLabel]
                        .filter(Boolean)
                        .join(" · ") || "No additional filters"}
                    </span>
                    <span className={styles.activityMeta}>
                      {formatActivityDate(search.searchedAt)}
                    </span>
                  </div>
                </article>
              ))}
            </div>
          )}

          <button
            type="button"
            className={styles.textLink}
            style={{ marginTop: 13 }}
            onClick={() => onNavigate("recent-searches")}
          >
            Open search activity →
          </button>
        </section>

        <section className={styles.featureCard} aria-labelledby="dashboard-views">
          <div className={styles.featureHead}>
            <h3 id="dashboard-views" className={styles.featureTitle}>
              Recently viewed
            </h3>
            <span className={styles.navCount}>
              {activity.recentViews.length}
            </span>
          </div>

          {featuredViews.length === 0 ? (
            <p className={styles.featureText}>
              Property and project pages you open will appear here so you
              can return to a detail preview.
            </p>
          ) : (
            <div className={styles.activityList} style={{ marginTop: 13 }}>
              {featuredViews.map((view) => (
                <article className={styles.activityRow} key={view.id}>
                  <div className={styles.activityMain}>
                    <span className={styles.activityKind}>{view.kind}</span>
                    <a className={styles.activityTitle} href={view.href}>
                      {view.title}
                    </a>
                    <span className={styles.activityMeta}>
                      {view.subtitle || "Location not supplied"}
                    </span>
                    <span className={styles.activityMeta}>
                      Viewed {formatActivityDate(view.viewedAt)}
                    </span>
                  </div>
                </article>
              ))}
            </div>
          )}

          <button
            type="button"
            className={styles.textLink}
            style={{ marginTop: 13 }}
            onClick={() => onNavigate("recent-views")}
          >
            Open viewed properties →
          </button>
        </section>
      </div>

      <div className={styles.sectionHeading}>
        <div>
          <h3>Your current shortlist</h3>
          <p>These are the saved records currently held by F06.</p>
        </div>

        <button
          type="button"
          className={styles.textLink}
          onClick={() => onNavigate("saved")}
        >
          View saved items →
        </button>
      </div>

      {featuredSaved.length === 0 ? (
        <div className={styles.emptyState}>
          <div className={styles.emptySymbol} aria-hidden="true">♡</div>
          <h3 className={styles.emptyTitle}>Your shortlist starts with a save.</h3>
          <p className={styles.emptyText}>
            Save a property or project from Search, or use the action bar
            on its detail page. The selection will appear in this account
            view while the current F06 session is alive.
          </p>
          <a className={`${styles.button} ${styles.buttonPrimary}`} href="/search">
            Discover properties and projects →
          </a>
        </div>
      ) : (
        <div className={styles.activityList}>
          {featuredSaved.map((record) => (
            <article
              className={styles.activityRow}
              key={`${record.kind}:${record.id}`}
            >
              <div className={styles.activityMain}>
                <span className={styles.activityKind}>{record.kind}</span>
                {record.href ? (
                  <a className={styles.activityTitle} href={record.href}>
                    {record.title}
                  </a>
                ) : (
                  <strong className={styles.activityTitle}>
                    {record.title}
                  </strong>
                )}
                <span className={styles.activityMeta}>
                  {[record.subtitle, record.detailLine]
                    .filter(Boolean)
                    .join(" · ") || "Further details not supplied"}
                </span>
              </div>

              {record.href ? (
                <div className={styles.activityActions}>
                  <a className={styles.smallButton} href={record.href}>
                    Reopen
                  </a>
                </div>
              ) : null}
            </article>
          ))}
        </div>
      )}

      <div className={styles.sectionHeading}>
        <div>
          <h3>Connected account services</h3>
          <p>Open a workspace to see its actual records or connection state.</p>
        </div>
      </div>

      <div className={styles.contentGrid}>
        {[
          {
            title: "Enquiry history",
            text: "Submitted enquiries and responses from the authorized enquiry service.",
            section: "enquiries" as const,
          },
          {
            title: "Conversations",
            text: "Messages and response timestamps from the connected inbox.",
            section: "conversations" as const,
          },
          {
            title: "Visit coordination",
            text: "Proposed and confirmed appointments reported by the visit service.",
            section: "visits" as const,
          },
          {
            title: "Recommendations",
            text: "Property matches returned by an approved recommendation source.",
            section: "recommendations" as const,
          },
        ].map((item) => (
          <button
            key={item.section}
            type="button"
            className={styles.featureCard}
            style={{ textAlign: "left", cursor: "pointer" }}
            onClick={() => onNavigate(item.section)}
          >
            <div className={styles.featureHead}>
              <h3 className={styles.featureTitle}>{item.title}</h3>
              <span className={styles.navIcon} aria-hidden="true">↗</span>
            </div>
            <p className={styles.featureText}>{item.text}</p>
          </button>
        ))}
      </div>

      <p className={styles.footer}>
        Signed in as {profile.email || displayNameFallback(profile.name)}.
        Email verification status comes from the identity provider.
        No enquiry, appointment or transaction status is inferred from browsing.
      </p>
    </>
  );
}

function displayNameFallback(name?: string): string {
  return name?.trim() || "HOMIO member";
}
