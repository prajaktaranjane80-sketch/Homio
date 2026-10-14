"use client";

import AIEmptyState from "./AIEmptyState";
import type { AIConversationMessage } from "./ai.types";
import styles from "./AIWorkspace.module.css";

type Props = Readonly<{
  messages: readonly AIConversationMessage[];
}>;

export default function AIConversationPreview({
  messages,
}: Props) {
  return (
    <section
      className={styles.card}
      aria-labelledby="ai-conversation-title"
    >
      <div className={styles.cardHeader}>
        <div>
          <p className={styles.kicker}>Your working notes</p>
          <h2 className={styles.cardTitle} id="ai-conversation-title">
            Conversation preview
          </h2>
        </div>

        <span className={styles.previewTag}>Local preview</span>
      </div>

      {messages.length > 0 ? (
        <div className={styles.messageList} aria-live="polite">
          {messages.map((message) => (
            <article
              className={
                message.role === "user"
                  ? styles.userMessage
                  : styles.assistantMessage
              }
              key={message.id}
            >
              <span className={styles.messageRole}>
                {message.role === "user" ? "YOUR BRIEF" : "WORKSPACE NOTE"}
              </span>

              <p>{message.content}</p>
            </article>
          ))}
        </div>
      ) : (
        <AIEmptyState
          title="Your brief will appear here"
          description="Choose a suggested prompt or describe your property goals. Submitting creates a local workflow preview, not a live AI answer."
        />
      )}

      <p className={styles.disclosure}>
        A live model is not connected. No property advice, market analysis or verification is generated here.
      </p>
    </section>
  );
}
