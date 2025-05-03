import { Interval, Subscription } from "@/lib/types/billing";

export async function getSubscription(
  accessToken: string,
  orgId: string,
): Promise<Subscription> {
  const response = await fetch(
    `${process.env.NEXT_PUBLIC_API_URL}/v1/billing/get-subscription`,
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
    throw new Error(`Failed to get subscription. Status: ${response.status}`);
  }
  return response.json();
}

export async function createCheckoutSession(
  accessToken: string,
  orgId: string,
  planName: string,
  interval: Interval,
): Promise<string> {
  const response = await fetch(
    `${process.env.NEXT_PUBLIC_API_URL}/v1/billing/create-checkout-session`,
    {
      method: "POST",
      headers: {
        "X-ACI-ORG-ID": orgId,
        "Content-Type": "application/json",
        Authorization: `Bearer ${accessToken}`,
      },
      body: JSON.stringify({
        plan_name: planName,
        interval,
      }),
    },
  );

  if (!response.ok) {
    throw new Error(
      `Failed to create checkout session. Status: ${response.status}`,
    );
  }
  return response.json();
}

export async function createCustomerPortalSession(
  accessToken: string,
  orgId: string,
): Promise<string> {
  const response = await fetch(
    `${process.env.NEXT_PUBLIC_API_URL}/v1/billing/create-customer-portal-session`,
    {
      method: "POST",
      headers: {
        "X-ACI-ORG-ID": orgId,
        "Content-Type": "application/json",
        Authorization: `Bearer ${accessToken}`,
      },
    },
  );

  if (!response.ok) {
    throw new Error(
      `Failed to create customer portal session. Status: ${response.status}`,
    );
  }
  return response.json();
}
