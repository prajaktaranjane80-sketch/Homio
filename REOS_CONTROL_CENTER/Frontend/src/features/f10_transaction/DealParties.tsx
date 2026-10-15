import {
  getInitials,
  PARTY_ROLE_LABELS,
} from "./transaction.constants";
import type { TransactionParty } from "./transaction.types";
import styles from "./TransactionWorkspace.module.css";

type Props = Readonly<{
  parties: readonly TransactionParty[];
}>;

export default function DealParties({ parties }: Props) {
  return (
    <section className={styles.panel} aria-labelledby="f10-parties-title">
      <div className={styles.panelHeader}>
        <div>
          <p className={styles.eyebrow}>PEOPLE & REPRESENTATIVES</p>
          <h2 className={styles.panelTitle} id="f10-parties-title">
            Transaction parties
          </h2>
          <p className={styles.panelDescription}>
            Participants supplied for this viewer.
          </p>
        </div>
        <span className={styles.countPill}>{parties.length}</span>
      </div>

      {parties.length === 0 ? (
        <p className={styles.emptyInline}>
          Participant information has not been supplied.
        </p>
      ) : (
        <ul className={styles.partyList}>
          {parties.map((party) => (
            <li className={styles.partyItem} key={party.id}>
              <span className={styles.partyAvatar} aria-hidden="true">
                {getInitials(party.displayName)}
              </span>

              <div className={styles.partyCopy}>
                <span className={styles.partyName}>
                  {party.displayName}
                </span>
                <span className={styles.partyRole}>
                  {PARTY_ROLE_LABELS[party.role]}
                </span>
                {party.organization ? (
                  <span className={styles.partyOrganization}>
                    {party.organization}
                  </span>
                ) : null}
                {party.contactLabel ? (
                  <span className={styles.partyContact}>
                    {party.contactLabel}
                  </span>
                ) : null}
              </div>
            </li>
          ))}
        </ul>
      )}

      <p className={styles.helperText}>
        Contact information should only be included when the transaction
        service authorizes it for the current viewer.
      </p>
    </section>
  );
}
