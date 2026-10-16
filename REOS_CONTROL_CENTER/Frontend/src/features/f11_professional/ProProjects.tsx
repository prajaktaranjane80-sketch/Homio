
import ProUnavailable from "./ProUnavailable";
import ProWorkspace from "./ProWorkspace";

export default function ProProjects() {
  return (
    <ProWorkspace section="projects">
      <ProUnavailable
        section="projects"
        capabilityKey="projects"
        title="Professional project access is not connected"
        description="Builder and project workflows must use verified project records and enforce the user's authorized role and organization scope."
        detail="Public discovery previews are not proof of professional ownership, builder authority, inventory rights or current project availability."
      />
    </ProWorkspace>
  );
}
