import { Button } from "@/components/ui/Button";

type Props = Readonly<{
  onRequestVisit?: () => void;
  disabled?: boolean;
  label?: string;
}>;

export function VisitButton({
  onRequestVisit,
  disabled = false,
  label = "Request a visit",
}: Props) {
  return (
    <Button
      type="button"
      variant="secondary"
      disabled={disabled || !onRequestVisit}
      onClick={onRequestVisit}
    >
      {label}
    </Button>
  );
}
