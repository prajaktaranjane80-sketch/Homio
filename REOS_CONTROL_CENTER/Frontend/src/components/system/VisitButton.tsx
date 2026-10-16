
/* File: src/components/system/VisitButton.tsx */
import { Button } from "@/components/ui/Button";

type Props = Readonly<{
  onVisit: () => void;
  disabled?: boolean;
  label?: string;
}>;

export default function VisitButton({
  onVisit,
  disabled = false,
  label = "Request a visit",
}: Props) {
  return (
    <Button
      type="button"
      disabled={disabled}
      onClick={onVisit}
    >
      {label}
    </Button>
  );
}
