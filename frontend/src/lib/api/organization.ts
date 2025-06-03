import { OrganizationMember } from "../types/organization";

export async function listOrganizationMembers(
  accessToken: string,
  orgId: string,
): Promise<OrganizationMember[]> {
  const response = await fetch(
    `${process.env.NEXT_PUBLIC_API_URL}/v1/organizations/members`,
    {
      headers: {
        Authorization: `Bearer ${accessToken}`,
        "X-ACI-ORG-ID": orgId,
      },
    },
  );

  if (!response.ok) {
    throw new Error("Failed to fetch organization members");
  }

  return response.json();
}

export async function inviteToOrganization(
  accessToken: string,
  orgId: string,
  email: string,
  role: string,
): Promise<void> {
  const response = await fetch(
    `${process.env.NEXT_PUBLIC_API_URL}/v1/organizations/invite`,
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${accessToken}`,
        "X-ACI-ORG-ID": orgId,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ email, role }),
    },
  );

  if (!response.ok) {
    throw new Error("Failed to invite user to organization");
  }
}

export async function removeMember(
  accessToken: string,
  orgId: string,
  userId: string,
): Promise<void> {
  const response = await fetch(
    `${process.env.NEXT_PUBLIC_API_URL}/v1/organizations/members/${userId}`,
    {
      method: "DELETE",
      headers: {
        Authorization: `Bearer ${accessToken}`,
        "X-ACI-ORG-ID": orgId,
      },
    },
  );

  if (!response.ok) {
    throw new Error("Failed to remove member");
  }
}

export async function leaveOrganization(
  accessToken: string,
  orgId: string,
): Promise<void> {
  const response = await fetch(
    `${process.env.NEXT_PUBLIC_API_URL}/v1/organizations/leave`,
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${accessToken}`,
        "X-ACI-ORG-ID": orgId,
      },
    },
  );

  if (!response.ok) {
    throw new Error("Failed to leave organization");
  }
}
