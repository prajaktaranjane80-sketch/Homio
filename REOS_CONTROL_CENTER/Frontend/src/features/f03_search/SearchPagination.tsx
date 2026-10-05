"use client";

import styles from "./SearchPagination.module.css";

type SearchPaginationProps = Readonly<{
  page: number;
  totalPages: number;
  onChange: (page: number) => void;
}>;

function createPages(page: number, totalPages: number): Array<number | "ellipsis"> {
  if (totalPages <= 7) {
    return Array.from({ length: totalPages }, (_, index) => index + 1);
  }

  if (page <= 4) {
    return [1, 2, 3, 4, 5, "ellipsis", totalPages];
  }

  if (page >= totalPages - 3) {
    return [
      1,
      "ellipsis",
      totalPages - 4,
      totalPages - 3,
      totalPages - 2,
      totalPages - 1,
      totalPages,
    ];
  }

  return [1, "ellipsis", page - 1, page, page + 1, "ellipsis", totalPages];
}

export default function SearchPagination({
  page,
  totalPages,
  onChange,
}: SearchPaginationProps) {
  if (totalPages <= 1) {
    return null;
  }

  const pages = createPages(page, totalPages);

  return (
    <nav className={styles.pagination} aria-label="Search result pages">
      <button
        type="button"
        className={styles.arrow}
        disabled={page <= 1}
        onClick={() => onChange(page - 1)}
        aria-label="Previous page"
      >
        ←
      </button>

      <div className={styles.pages}>
        {pages.map((item, index) =>
          item === "ellipsis" ? (
            <span key={`ellipsis-${index}`} className={styles.ellipsis}>
              …
            </span>
          ) : (
            <button
              key={item}
              type="button"
              className={`${styles.page} ${
                item === page ? styles.active : ""
              }`}
              aria-current={item === page ? "page" : undefined}
              onClick={() => onChange(item)}
            >
              {item}
            </button>
          ),
        )}
      </div>

      <button
        type="button"
        className={styles.arrow}
        disabled={page >= totalPages}
        onClick={() => onChange(page + 1)}
        aria-label="Next page"
      >
        →
      </button>
    </nav>
  );
}
