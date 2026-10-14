import type {
  CompareFieldGroup,
  CompareItem,
} from "./compare.types";

import styles from "./SavedCompareExperience.module.css";

type CompareTableProps = Readonly<{
  items: readonly CompareItem[];
  selectedGroups: readonly CompareFieldGroup[];

  onRemove?: (
    id: string,
    kind: CompareItem["kind"],
  ) => void;
}>;

type ComparisonRow = {
  label: string;
  group: CompareFieldGroup;
  values: Map<
    string,
    string | number | null | undefined
  >;
};

function itemIdentity(item: CompareItem): string {
  return `${item.kind}:${item.id}`;
}

function displayValue(
  value: string | number | null | undefined,
): string {
  if (
    value === null ||
    value === undefined ||
    String(value).trim() === ""
  ) {
    return "Not supplied";
  }

  return String(value);
}

export default function CompareTable({
  items,
  selectedGroups,
  onRemove,
}: CompareTableProps) {
  const rows = new Map<string, ComparisonRow>();

  for (const item of items) {
    const identity = itemIdentity(item);

    for (const field of item.fields) {
      if (!selectedGroups.includes(field.group)) {
        continue;
      }

      const rowKey =
        `${field.group}:` +
        field.label.trim().toLocaleLowerCase();

      let row = rows.get(rowKey);

      if (!row) {
        row = {
          label: field.label,
          group: field.group,
          values: new Map(),
        };

        rows.set(rowKey, row);
      }

      row.values.set(identity, field.value);
    }
  }

  if (items.length === 0) {
    return null;
  }

  if (rows.size === 0) {
    return (
      <div className={styles.tableNotice}>
        Choose at least one comparison group to show details.
      </div>
    );
  }

  return (
    <div
      className={styles.tableScroll}
      role="region"
      aria-label="Property and project comparison table"
      tabIndex={0}
    >
      <table className={styles.compareTable}>
        <thead>
          <tr>
            <th
              scope="col"
              className={styles.attributeHead}
            >
              Decision detail
            </th>

            {items.map((item) => {
              const identity = itemIdentity(item);

              return (
                <th scope="col" key={identity}>
                  <div className={styles.compareColumn}>
                    <span className={styles.compareKind}>
                      {item.kind}
                    </span>

                    <strong>{item.title}</strong>

                    {item.subtitle ? (
                      <span className={styles.compareSubtitle}>
                        {item.subtitle}
                      </span>
                    ) : null}

                    {item.href ? (
                      <a
                        className={styles.columnLink}
                        href={item.href}
                      >
                        Open details
                        <span aria-hidden="true"> ↗</span>
                      </a>
                    ) : null}

                    {onRemove ? (
                      <button
                        className={styles.quietAction}
                        type="button"
                        onClick={() =>
                          onRemove(item.id, item.kind)
                        }
                        aria-label={
                          `Remove ${item.title} from comparison`
                        }
                      >
                        Remove
                      </button>
                    ) : null}
                  </div>
                </th>
              );
            })}
          </tr>
        </thead>

        <tbody>
          {Array.from(rows.entries()).map(
            ([rowKey, row]) => (
              <tr key={rowKey}>
                <th scope="row">
                  <span className={styles.groupLabel}>
                    {row.group}
                  </span>

                  <strong>{row.label}</strong>
                </th>

                {items.map((item) => {
                  const identity = itemIdentity(item);
                  const value = row.values.get(identity);

                  const missing =
                    value === undefined ||
                    value === null ||
                    String(value).trim() === "";

                  return (
                    <td
                      key={identity}
                      className={
                        missing
                          ? styles.missingValue
                          : undefined
                      }
                    >
                      {displayValue(value)}
                    </td>
                  );
                })}
              </tr>
            ),
          )}
        </tbody>
      </table>
    </div>
  );
}
