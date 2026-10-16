
/* File: src/components/system/StatusBadge.tsx */
import styles from "./SharedSystem.module.css";

export type SystemStatus =
  | "active"
  | "built"
  | "pending"
  | "verified"
  | "unverified"
  | "success"
  | "warning"
  | "error"
  | "unavailable"
  | "draft";

const STATUS_LABELS: Record<SystemStatus, string> = {
  active: "Active",
  built: "Built · Not live",
  pending: "Pending",
  verified: "Verified",
  unverified: "Not verified",
  success: "Complete",
  warning: "Needs attention",
  error: "Error",
  unavailable: "Unavailable",
  draft: "Draft",
};

function statusClass(status: SystemStatus): string {
  if (status === "active" || status === "verified" || status === "success") {
    return styles.badgePositive;
  }

  if (status === "built" || status === "pending" || status === "warning" ||
      status === "unverified" || status === "draft") {
    return styles.badgeWarning;
  }

  if (status === "error") return styles.badgeError;

  return styles.badgeNeutral;
}

type Props = Readonly<{
  status: SystemStatus;
  label?: string;
}>;

export default function StatusBadge({ status, label }: Props) {
  return (
    <span className={`${styles.systemBadge} ${statusClass(status)}`}>
      {label ?? STATUS_LABELS[status]}
    </span>
  );
}
