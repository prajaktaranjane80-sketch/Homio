
import ProUnavailable from "./ProUnavailable";
import ProWorkspace from "./ProWorkspace";

export default function ProFollowUps() {
  return (
    <ProWorkspace section="follow-ups">
      <ProUnavailable
        section="follow-ups"
        capabilityKey="followUps"
        title="Follow-ups need a verified source"
        description="A follow-up should be shown only when it comes from an authorized enquiry, visit, communication or transaction workflow."
        detail="No deadlines, reminders or pending actions are fabricated. Completing an action will require a verified server response."
      />
    </ProWorkspace>
  );
}
