import { LinkedAccount } from "@/lib/types/linkedaccount";

export async function getAllLinkedAccounts(
  apiKey: string,
): Promise<LinkedAccount[]> {
  const response = await fetch(
    `${process.env.NEXT_PUBLIC_API_URL}/v1/linked-accounts`,
    {
      method: "GET",
      headers: {
        "X-API-KEY": apiKey,
      },
    },
  );

  if (!response.ok) {
    throw new Error(
      `Failed to fetch all linked accounts: ${response.status} ${response.statusText}`,
    );
  }

  const linkedAccounts = await response.json();
  return linkedAccounts;
}

export async function getAppLinkedAccounts(
  appName: string,
  apiKey: string,
): Promise<LinkedAccount[]> {
  const params = new URLSearchParams();
  params.append("app_name", appName);

  const response = await fetch(
    `${
      process.env.NEXT_PUBLIC_API_URL
    }/v1/linked-accounts?${params.toString()}`,
    {
      method: "GET",
      headers: {
        "X-API-KEY": apiKey,
      },
    },
  );

  if (!response.ok) {
    throw new Error(
      `Failed to fetch linked accounts: ${response.status} ${response.statusText}`,
    );
  }

  const linkedAccounts = await response.json();
  return linkedAccounts;
}

export async function createAPILinkedAccount(
  appName: string,
  linkedAccountOwnerId: string,
  linkedAPIKey: string,
  apiKey: string,
): Promise<LinkedAccount> {
  const response = await fetch(
    `${process.env.NEXT_PUBLIC_API_URL}/v1/linked-accounts/api-key`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-API-KEY": apiKey,
      },
      body: JSON.stringify({
        app_name: appName,
        linked_account_owner_id: linkedAccountOwnerId,
        api_key: linkedAPIKey,
      }),
    },
  );

  if (!response.ok) {
    let errorMsg = `Failed to create linked account: ${response.status} ${response.statusText}`;
    try {
      const errorData = await response.json();
      if (errorData && errorData.error) {
        errorMsg = errorData.error;
      }
    } catch (e) {
      console.error("Error parsing error response:", e);
    }
    throw new Error(errorMsg);
  }

  const linkedAccount = await response.json();
  return linkedAccount;
}

export async function createNoAuthLinkedAccount(
  appName: string,
  linkedAccountOwnerId: string,
  apiKey: string,
): Promise<LinkedAccount> {
  const response = await fetch(
    `${process.env.NEXT_PUBLIC_API_URL}/v1/linked-accounts/no-auth`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-API-KEY": apiKey,
      },
      body: JSON.stringify({
        app_name: appName,
        linked_account_owner_id: linkedAccountOwnerId,
      }),
    },
  );

  if (!response.ok) {
    let errorMsg = `Failed to create no auth linked account: ${response.status} ${response.statusText}`;
    try {
      const errorData = await response.json();
      if (errorData && errorData.error) {
        errorMsg = errorData.error;
      }
    } catch (e) {
      console.error("Error parsing error response:", e);
    }
    throw new Error(errorMsg);
  }

  const linkedAccount = await response.json();
  return linkedAccount;
}

export async function getOauth2LinkURL(
  appName: string,
  linkedAccountOwnerId: string,
  apiKey: string,
  afterOAuth2LinkRedirectURL?: string,
): Promise<string> {
  const params = new URLSearchParams();
  params.append("app_name", appName);
  params.append("linked_account_owner_id", linkedAccountOwnerId);
  if (afterOAuth2LinkRedirectURL) {
    params.append("after_oauth2_link_redirect_url", afterOAuth2LinkRedirectURL);
  }

  const response = await fetch(
    `${
      process.env.NEXT_PUBLIC_API_URL
    }/v1/linked-accounts/oauth2?${params.toString()}`,
    {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        "X-API-KEY": apiKey,
      },
    },
  );

  if (!response.ok) {
    let errorMsg = `Failed to get OAuth2 link URL: ${response.status} ${response.statusText}`;
    try {
      const errorData = await response.json();
      if (errorData && errorData.error) {
        errorMsg = errorData.error;
      }
    } catch (e) {
      console.error("Error parsing error response:", e);
    }
    throw new Error(errorMsg);
  }

  const data = await response.json();
  if (!data.url || typeof data.url !== "string") {
    throw new Error("Invalid response: missing or invalid URL");
  }
  return data.url;
}

export async function deleteLinkedAccount(
  linkedAccountId: string,
  apiKey: string,
): Promise<void> {
  const response = await fetch(
    `${process.env.NEXT_PUBLIC_API_URL}/v1/linked-accounts/${linkedAccountId}`,
    {
      method: "DELETE",
      headers: {
        "X-API-KEY": apiKey,
      },
    },
  );

  if (!response.ok) {
    throw new Error(
      `Failed to delete linked account: ${response.status} ${response.statusText}`,
    );
  }
}

export async function updateLinkedAccount(
  linkedAccountId: string,
  apiKey: string,
  enabled: boolean,
): Promise<LinkedAccount> {
  const response = await fetch(
    `${process.env.NEXT_PUBLIC_API_URL}/v1/linked-accounts/${linkedAccountId}`,
    {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        "X-API-KEY": apiKey,
      },
      body: JSON.stringify({
        enabled,
      }),
    },
  );

  if (!response.ok) {
    throw new Error(
      `Failed to update linked account: ${response.status} ${response.statusText}`,
    );
  }

  const updatedLinkedAccount = await response.json();
  return updatedLinkedAccount;
}
