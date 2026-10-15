import type { Metadata } from "next";

import EnquiryShell from "@/features/f09_enquiry_visit/EnquiryShell";
import type { EnquiryTarget } from "@/features/f09_enquiry_visit/enquiry.types";

export const metadata: Metadata = {
  title: "Contact HOMIO | Enquiry Preview",
  description:
    "Prepare a property-related question or general enquiry in the HOMIO experience preview.",
  robots: {
    index: false,
    follow: true,
  },
};

const GENERAL_ENQUIRY_TARGET: EnquiryTarget = {
  kind: "general",
  title: "General HOMIO enquiry",
};

export default function EnquiryRoute() {
  return <EnquiryShell target={GENERAL_ENQUIRY_TARGET} />;
}
