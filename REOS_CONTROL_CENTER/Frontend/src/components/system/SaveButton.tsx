import { Button } from "@/components/ui/Button";

type Props = Readonly<{
  saved: boolean;
  onSave?: () => void;
  disabled?: boolean;
  label?: string;
}>;

export function SaveButton({ saved, onSave, disabled = false, label }: Props) {
  return (
    <Button
      type="button"
      variant={saved ? "secondary" : "primary"}
      aria-pressed={saved}
      disabled={disabled || !onSave}
      onClick={onSave}
    >
      {label ?? (saved ? "Saved" : "Save")}
    </Button>
  );
}
