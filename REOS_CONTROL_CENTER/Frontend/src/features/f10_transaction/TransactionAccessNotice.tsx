import type { TransactionViewerRole } from "./transaction.types";
import { humanizeCode } from "./transaction.constants";
import styles from "./TransactionWorkspace.module.css";

type Props = Readonly<{
  viewerRole?: TransactionViewerRole;
}>;

export default function TransactionAccessNotice({
  viewerRole,
}: Props) {
  return (
    <aside className={styles.accessNotice} aria-label="Transaction data notice">
      <span className={styles.accessIcon} aria-hidden="true">
        ◈
      </span>

      <div className={styles.accessCopy}>
        <p className={styles.accessTitle}>
          Your transaction workspace
          {viewerRole ? ` · ${humanizeCode(viewerRole)}` : ""}
        </p>
        <p className={styles.accessText}>
          This view presents the transaction information supplied for this
          viewer. The server remains responsible for access permissions and
          authorizing every action.
        </p>
      </div>
    </aside>
  );
}
