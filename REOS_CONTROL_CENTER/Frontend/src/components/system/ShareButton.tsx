
/* File: src/components/system/ShareButton.tsx */
import { Button } from "@/components/ui/Button";

type Props = Readonly<{
  onShare: () => void;
  disabled?: boolean;
}>;

export default function ShareButton({
  onShare,
  disabled = false,
}: Props) {
  return (
    <Button
      type="button"
      variant="ghost"
      size="small"
      disabled={disabled}
      onClick={onShare}
    >
      Share
    </Button>
  );
}
