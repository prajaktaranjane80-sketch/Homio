
import ProUnavailable from "./ProUnavailable";
import ProWorkspace from "./ProWorkspace";

export default function ProEnquiries() {
  return (
    <ProWorkspace section="enquiries">
      <ProUnavailable
        section="enquiries"
        capabilityKey="enquiries"
        title="Enquiry history is not connected yet"
        description="Property and project enquiries must come from the authorized enquiry service, with access limited to the appropriate user and organization."
        detail="This workspace does not invent enquiry reference numbers, buyer details, status updates or successful contact outcomes."
      />
    </ProWorkspace>
  );
}
