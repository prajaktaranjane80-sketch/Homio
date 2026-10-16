
import ProUnavailable from "./ProUnavailable";
import ProWorkspace from "./ProWorkspace";

export default function ProVisits() {
  return (
    <ProWorkspace section="visits">
      <ProUnavailable
        section="visits"
        capabilityKey="visits"
        title="Visit scheduling requires a verified service"
        description="Visit requests, confirmed appointments, video walkthroughs, cancellations and rescheduling must reflect the authoritative scheduling service."
        detail="No appointment is presented as confirmed, and no visit is booked, cancelled or rescheduled by this preview."
      />
    </ProWorkspace>
  );
}
