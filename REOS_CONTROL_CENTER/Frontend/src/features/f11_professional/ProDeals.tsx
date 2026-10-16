
import ProUnavailable from "./ProUnavailable";
import ProWorkspace from "./ProWorkspace";

export default function ProDeals() {
  return (
    <ProWorkspace section="deals">
      <ProUnavailable
        section="deals"
        capabilityKey="deals"
        title="Deal information remains under REOS authority"
        description="Deal status, parties, negotiation history, milestones and next actions can appear only after the transaction service authorizes the current user for the requested deal."
        detail="This preview does not simulate a deal, negotiation, completion, commission or successful business action."
      />
    </ProWorkspace>
  );
}
