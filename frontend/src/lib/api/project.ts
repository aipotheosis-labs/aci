import { Project } from "@/lib/types/project";

export async function getProjects(
  accessToken: string,
  orgId: string,
): Promise<Project[]> {
  const response = await fetch(
    `${process.env.NEXT_PUBLIC_API_URL}/v1/projects`,
    {
      method: "GET",
      headers: {
        "X-ACI-ORG-ID": orgId,
        Authorization: `Bearer ${accessToken}`,
      },
      credentials: "include",
    },
  );

  if (!response.ok) {
    throw new Error(
      `Failed to fetch projects: ${response.status} ${response.statusText}`,
    );
  }
  const retrievedProjects: Project[] = await response.json();
  return retrievedProjects;
}

export async function createProject(
  accessToken: string,
  name: string,
  orgId: string,
): Promise<Project> {
  const response = await fetch(
    `${process.env.NEXT_PUBLIC_API_URL}/v1/projects`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${accessToken}`,
      },
      credentials: "include",
      body: JSON.stringify({ name, org_id: orgId }),
    },
  );

  if (!response.ok) {
    throw new Error(
      `Failed to create project: ${response.status} ${response.statusText}`,
    );
  }

  const createdProject: Project = await response.json();
  return createdProject;
}
