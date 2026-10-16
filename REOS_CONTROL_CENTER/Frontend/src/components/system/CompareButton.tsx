import { Button } from "@/components/ui/Button";

type Props = Readonly<{
  compared: boolean;
  onToggle?: () => void;
  disabled?: boolean;
}>;

export function CompareButton({ compared, onToggle, disabled = false }: Props) {
  return (
    <Button
      type="button"
      variant="secondary"
      aria-pressed={compared}
      disabled={disabled || !onToggle}
      onClick={onToggle}
    >
      {compared ? "In compare" : "Compare"}
    </Button>
  );
}
