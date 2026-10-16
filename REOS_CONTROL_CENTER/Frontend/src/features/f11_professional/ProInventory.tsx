
import ProUnavailable from "./ProUnavailable";
import ProWorkspace from "./ProWorkspace";

export default function ProInventory() {
  return (
    <ProWorkspace section="inventory">
      <ProUnavailable
        section="inventory"
        capabilityKey="inventory"
        title="Your authorized inventory, in one workspace"
        description="The inventory interface is prepared, but property records cannot be shown until the current professional role, organization scope and record permissions are verified."
        detail="No listings, prices, ownership details, verification badges or availability claims are fabricated for this preview."
      />
    </ProWorkspace>
  );
}
