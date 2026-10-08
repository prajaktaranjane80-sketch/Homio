import ProjectUnavailable from "@/features/f05_project/ProjectUnavailable";

export default function ProjectNotFound() {
  return (
    <ProjectUnavailable
      title="We couldn't find this project."
      description="The project reference may be unavailable, expired or not accessible in the current HOMIO experience."
    />
  );
}
