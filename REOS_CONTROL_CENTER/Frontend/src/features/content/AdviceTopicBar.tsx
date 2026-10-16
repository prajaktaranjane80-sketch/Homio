import Link from "next/link";

import styles from "./ContentExperience.module.css";
import type { ContentLink } from "./ContentExperience.types";

type Props = Readonly<{
  topics: readonly ContentLink[];
  label?: string;
}>;

export default function AdviceTopicBar({
  topics,
  label = "Browse topics",
}: Props) {
  if (topics.length === 0) return null;

  return (
    <nav className={styles.contentTopicBar} aria-label={label}>
      {topics.map((topic) => (
        <Link className={styles.contentTopic} href={topic.href} key={topic.id}>
          {topic.title}
        </Link>
      ))}
    </nav>
  );
}
