
/* File: src/components/system/CompareButton.tsx */
import { Button } from "@/components/ui/Button";

type Props = Readonly<{
  selected: boolean;
  onToggle: () => void;
  disabled?: boolean;
}>;

export default function CompareButton({
  selected,
  onToggle,
  disabled = false,
}: Props) {
  return (
    <Button
      type="button"
      variant={selected ? "secondary" : "ghost"}
      size="small"
      aria-pressed={selected}
      disabled={disabled}
      onClick={onToggle}
    >
      {selected ? "In compare" : "Compare"}
    </Button>
  );
}
