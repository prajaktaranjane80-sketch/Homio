
/* File: src/components/system/EnquiryButton.tsx */
import { Button } from "@/components/ui/Button";

type Props = Readonly<{
  onEnquiry: () => void;
  disabled?: boolean;
  label?: string;
}>;

export default function EnquiryButton({
  onEnquiry,
  disabled = false,
  label = "Make an enquiry",
}: Props) {
  return (
    <Button
      type="button"
      disabled={disabled}
      onClick={onEnquiry}
    >
      {label}
    </Button>
  );
}
