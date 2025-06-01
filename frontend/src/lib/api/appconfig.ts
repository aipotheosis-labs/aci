import { AppConfig } from "@/lib/types/appconfig";

export async function getAppConfig(
  appName: string,
  apiKey: string,
): Promise<AppConfig | null> {
  const params = new URLSearchParams();
  params.append("app_names", appName);

  const response = await fetch(
    `${
      process.env.NEXT_PUBLIC_API_URL
    }/v1/app-configurations?${params.toString()}`,
    {
      method: "GET",
      headers: {
        "X-API-KEY": apiKey,
      },
    },
  );

  if (!response.ok) {
    throw new Error(`Failed to fetch app configuration`);
  }

  const configs = await response.json();
  return configs.length > 0 ? configs[0] : null;
}

export async function getAllAppConfigs(apiKey: string): Promise<AppConfig[]> {
  const response = await fetch(
    `${process.env.NEXT_PUBLIC_API_URL}/v1/app-configurations`,
    {
      method: "GET",
      headers: {
        "X-API-KEY": apiKey,
      },
    },
  );

  if (!response.ok) {
    throw new Error(
      `Failed to fetch app configurations: ${response.status} ${response.statusText}`,
    );
  }

  const appConfigs = await response.json();
  return appConfigs;
}

export class AppAlreadyConfiguredError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "AppAlreadyConfiguredError";
    Object.setPrototypeOf(this, new.target.prototype); // Restore prototype chain
  }
}

export async function createAppConfig(
  appName: string,
  security_scheme: string,
  apiKey: string,
  security_scheme_overrides?: {
    oauth2?: {
      client_id: string;
      client_secret: string;
      redirect_url?: string;
    } | null;
  },
): Promise<AppConfig> {
  const response = await fetch(
    `${process.env.NEXT_PUBLIC_API_URL}/v1/app-configurations`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-API-KEY": apiKey,
      },
      body: JSON.stringify({
        app_name: appName,
        security_scheme: security_scheme,
        security_scheme_overrides: security_scheme_overrides ?? {},
        all_functions_enabled: true,
        enabled_functions: [],
      }),
    },
  );

  if (response.status === 409) {
    throw new AppAlreadyConfiguredError(
      `App configuration already exists for app: ${appName}`,
    );
  }

  if (!response.ok) {
    throw new Error(
      `Failed to configure app: ${response.status} ${response.statusText}`,
    );
  }

  const appConfig = await response.json();
  return appConfig;
}

export async function updateAppConfig(
  appName: string,
  enabled: boolean,
  apiKey: string,
): Promise<AppConfig> {
  const response = await fetch(
    `${process.env.NEXT_PUBLIC_API_URL}/v1/app-configurations/${appName}`,
    {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        "X-API-KEY": apiKey,
      },
      body: JSON.stringify({
        enabled: enabled,
      }),
    },
  );

  if (!response.ok) {
    throw new Error(
      `Failed to update app configuration for ${appName}: ${response.status} ${response.statusText}`,
    );
  }

  const appConfig = await response.json();
  return appConfig;
}

export async function deleteAppConfig(
  appName: string,
  apiKey: string,
): Promise<Response> {
  const response = await fetch(
    `${process.env.NEXT_PUBLIC_API_URL}/v1/app-configurations/${appName}`,
    {
      method: "DELETE",
      headers: {
        "Content-Type": "application/json",
        "X-API-KEY": apiKey,
      },
    },
  );

  if (!response.ok) {
    throw new Error(
      `Failed to delete app configuration for ${appName}: ${response.status} ${response.statusText}`,
    );
  }

  return response;
}
