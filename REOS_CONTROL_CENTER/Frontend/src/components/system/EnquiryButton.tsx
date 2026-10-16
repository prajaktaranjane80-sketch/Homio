import { Button } from "@/components/ui/Button";

type Props = Readonly<{
  onEnquire?: () => void;
  disabled?: boolean;
  label?: string;
}>;

export function EnquiryButton({
  onEnquire,
  disabled = false,
  label = "Make an enquiry",
}: Props) {
  return (
    <Button
      type="button"
      disabled={disabled || !onEnquire}
      onClick={onEnquire}
    >
      {label}
    </Button>
  );
}
