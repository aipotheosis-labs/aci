import { Project } from "@/lib/types/project";

export function getApiKey(project: Project, agentId?: string): string {
  if (
    !project ||
    !project.agents ||
    project.agents.length === 0 ||
    !project.agents[0].api_keys ||
    project.agents[0].api_keys.length === 0
  ) {
    throw new Error(
      `No API key available in project: ${project.id} ${project.name}`,
    );
  }
  if (agentId) {
    const agent = project.agents.find((agent) => agent.id === agentId);
    if (!agent) {
      throw new Error(`Agent ${agentId} not found in project ${project.id}`);
    }
    return agent.api_keys[0].key;
  }
  return project.agents[0].api_keys[0].key;
}
