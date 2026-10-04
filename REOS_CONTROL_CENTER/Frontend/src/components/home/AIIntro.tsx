import Link from "next/link";
import styles from "./AIIntro.module.css";

type Props = {
  suggestions: string[];
};

export default function AIIntro({ suggestions }: Props) {
  return (
    <div className={styles.content}>
      <span className={styles.eyebrow}>HOMIO AI</span>

      <h2>
        Search less.
        <br />
        Understand more.
      </h2>

      <p>
        HOMIO AI helps turn property discovery into a conversation. Refine
        what you want, ask questions and move toward the next useful action.
      </p>

      <div className={styles.actions}>
        <Link href="/ai" className={styles.primary}>
          Open HOMIO AI
          <span aria-hidden="true">↗</span>
        </Link>

        <Link href="/search" className={styles.secondary}>
          Continue normal search
        </Link>
      </div>

      <div className={styles.suggestions}>
        <span>TRY ASKING</span>

        <div>
          {suggestions.map((suggestion) => (
            <Link key={suggestion} href="/ai">
              {suggestion}
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
