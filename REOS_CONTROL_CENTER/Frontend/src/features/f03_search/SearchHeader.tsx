import styles from "./SearchHeader.module.css";

type SearchHeaderProps = Readonly<{
  title: string;
  description: string;
}>;

export default function SearchHeader({
  title,
  description,
}: SearchHeaderProps) {
  return (
    <header className={styles.header}>
      <span className={styles.eyebrow}>HOMIO SEARCH</span>

      <h1 className={styles.title}>{title}</h1>

      <p className={styles.description}>{description}</p>
    </header>
  );
}
