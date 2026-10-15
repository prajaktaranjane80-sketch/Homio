import {
  formatDate,
  MILESTONE_STATUS_META,
  TONE_CLASS_KEY,
} from "./transaction.constants";
import type { TransactionMilestone } from "./transaction.types";
import styles from "./TransactionWorkspace.module.css";

type Props = Readonly<{
  milestones: readonly TransactionMilestone[];
}>;

export default function TransactionMilestones({ milestones }: Props) {
  return (
    <section className={styles.panel} aria-labelledby="f10-milestones-title">
      <div className={styles.panelHeader}>
        <div>
          <p className={styles.eyebrow}>PROGRESS & DEPENDENCIES</p>
          <h2 className={styles.panelTitle} id="f10-milestones-title">
            Transaction milestones
          </h2>
          <p className={styles.panelDescription}>
            Milestone order and states returned by the transaction service.
          </p>
        </div>
        <span className={styles.countPill}>{milestones.length}</span>
      </div>

      {milestones.length === 0 ? (
        <p className={styles.emptyInline}>
          No transaction milestones have been supplied.
        </p>
      ) : (
        <ol className={styles.milestoneList}>
          {milestones.map((milestone, index) => {
            const meta = MILESTONE_STATUS_META[milestone.status];

            return (
              <li className={styles.milestoneItem} key={milestone.id}>
                <div className={styles.milestoneRail} aria-hidden="true">
                  <span
                    className={`${styles.milestoneDot} ${
                      milestone.status === "completed"
                        ? styles.milestoneDotCompleted
                        : milestone.status === "blocked" ||
                            milestone.status === "delayed"
                          ? styles.milestoneDotAttention
                          : ""
                    }`}
                  >
                    {milestone.status === "completed" ? "✓" : index + 1}
                  </span>
                  {index < milestones.length - 1 ? (
                    <span className={styles.milestoneConnector} />
                  ) : null}
                </div>

                <div className={styles.milestoneBody}>
                  <div className={styles.milestoneTitleRow}>
                    <h3 className={styles.itemTitle}>{milestone.title}</h3>
                    <span
                      className={`${styles.statusBadge} ${styles[TONE_CLASS_KEY[meta.tone]]}`}
                    >
                      <span className={styles.statusDot} aria-hidden="true" />
                      {meta.label}
                    </span>
                  </div>

                  {milestone.description ? (
                    <p className={styles.itemDescription}>
                      {milestone.description}
                    </p>
                  ) : null}

                  <div className={styles.activityMeta}>
                    <span>
                      Target: {formatDate(milestone.targetAt)}
                    </span>
                    {milestone.updatedAt ? (
                      <span>
                        Updated {formatDate(milestone.updatedAt)}
                      </span>
                    ) : null}
                  </div>
                </div>
              </li>
            );
          })}
        </ol>
      )}

      <p className={styles.helperText}>
        The timeline is presented in the order supplied. The frontend does not
        infer dependencies or mark milestones complete.
      </p>
    </section>
  );
}
