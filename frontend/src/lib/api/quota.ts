import { QuotaUsage } from "@/lib/types/quota";

export async function getQuotaUsage(
  accessToken: string,
  orgId: string,
): Promise<QuotaUsage> {
  const response = await fetch(
    `${process.env.NEXT_PUBLIC_API_URL}/v1/billing/quota-usage`,
    {
      method: "GET",
      headers: {
        "X-ACI-ORG-ID": orgId,
        "Content-Type": "application/json",
        Authorization: `Bearer ${accessToken}`,
      },
    },
  );

  if (!response.ok) {
    throw new Error(`Failed to get quota usage. Status: ${response.status}`);
  }
  return response.json();
}
