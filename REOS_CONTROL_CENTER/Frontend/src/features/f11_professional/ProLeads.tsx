
import ProUnavailable from "./ProUnavailable";
import ProWorkspace from "./ProWorkspace";

export default function ProLeads() {
  return (
    <ProWorkspace section="leads">
      <ProUnavailable
        section="leads"
        capabilityKey="leads"
        title="Authorized lead records will appear here"
        description="Lead ownership, contact information, qualification and status must be returned by the approved REOS lead service for the authenticated professional."
        detail="No sample contacts, lead counts, conversion rates or follow-up claims are generated. Record access and every future action require server-side authorization."
      />
    </ProWorkspace>
  );
}
