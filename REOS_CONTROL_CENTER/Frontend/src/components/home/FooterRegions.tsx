import styles from "./FooterRegions.module.css";

const regions = [
  "Americas",
  "Europe",
  "Middle East",
  "Asia Pacific",
];

export default function FooterRegions() {
  return (
    <div className={styles.wrapper}>
      {regions.map((region) => (
        <span key={region}>{region}</span>
      ))}
    </div>
  );
}
