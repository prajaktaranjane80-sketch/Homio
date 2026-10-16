
import ProUnavailable from "./ProUnavailable";
import ProWorkspace from "./ProWorkspace";

export default function ProClients() {
  return (
    <ProWorkspace section="clients">
      <ProUnavailable
        section="clients"
        capabilityKey="clients"
        title="Client records stay access-controlled"
        description="Client profiles and contact details must be supplied by an authorized REOS capability and scoped to the permitted user and organization."
        detail="No fabricated client profiles or contact details are shown. Do not expose client information through browser storage, URLs or logs."
      />
    </ProWorkspace>
  );
}
