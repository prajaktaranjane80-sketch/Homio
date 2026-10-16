import { Button } from "@/components/ui/Button";

type Props = Readonly<{
  onShare?: () => void;
  disabled?: boolean;
  label?: string;
}>;

export function ShareButton({ onShare, disabled = false, label = "Share" }: Props) {
  return (
    <Button
      type="button"
      variant="secondary"
      disabled={disabled || !onShare}
      onClick={onShare}
    >
      {label}
    </Button>
  );
}
