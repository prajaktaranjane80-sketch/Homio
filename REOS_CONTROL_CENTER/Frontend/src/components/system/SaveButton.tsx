
/* File: src/components/system/SaveButton.tsx */
import { Button } from "@/components/ui/Button";

type Props = Readonly<{
  saved: boolean;
  onSave: () => void;
  disabled?: boolean;
}>;

export default function SaveButton({
  saved,
  onSave,
  disabled = false,
}: Props) {
  return (
    <Button
      type="button"
      variant={saved ? "secondary" : "ghost"}
      size="small"
      aria-pressed={saved}
      disabled={disabled}
      onClick={onSave}
    >
      {saved ? "Saved" : "Save"}
    </Button>
  );
}
