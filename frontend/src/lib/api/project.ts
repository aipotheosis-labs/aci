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
    const errorData = await response.json().catch(() => null);
    const errorMessage =
      errorData?.error ||
      `Failed to create project: ${response.status} ${response.statusText}`;
    throw new Error(errorMessage);
  }

  const createdProject: Project = await response.json();
  return createdProject;
}

export async function updateProject(
  accessToken: string,
  projectId: string,
  name: string,
): Promise<Project> {
  const response = await fetch(
    `${process.env.NEXT_PUBLIC_API_URL}/v1/projects/${projectId}`,
    {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${accessToken}`,
      },
      credentials: "include",
      body: JSON.stringify({ name }),
    },
  );

  if (!response.ok) {
    throw new Error(
      `Failed to update project: ${response.status} ${response.statusText}`,
    );
  }

  const updatedProject: Project = await response.json();
  return updatedProject;
}

export async function deleteProject(
  accessToken: string,
  projectId: string,
): Promise<void> {
  const response = await fetch(
    `${process.env.NEXT_PUBLIC_API_URL}/v1/projects/${projectId}`,
    {
      method: "DELETE",
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
      credentials: "include",
    },
  );

  if (!response.ok) {
    throw new Error(
      `Failed to delete project: ${response.status} ${response.statusText}`,
    );
  }
}
