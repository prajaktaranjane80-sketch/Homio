
/* File: src/components/system/ErrorRetry.tsx */
import { ErrorState } from "@/components/ui/ErrorState";

type Props = Readonly<{
  title?: string;
  description: string;
  onRetry: () => void;
  retryDisabled?: boolean;
}>;

export default function ErrorRetry({
  title = "We couldn't load this section",
  description,
  onRetry,
  retryDisabled = false,
}: Props) {
  return (
    <div aria-live="polite">
      <ErrorState
        title={title}
        description={description}
        actionLabel="Try again"
        onAction={onRetry}
      />
      {retryDisabled ? (
        <p role="status">Retry is temporarily unavailable.</p>
      ) : null}
    </div>
  );
}
