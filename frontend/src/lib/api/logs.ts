import { LogSearchResponse } from "@/lib/types/logs";

export async function searchLogs(
  apiKey: string,
  page: number = 1,
  pageSize: number = 20,
  appName?: string,
  functionName?: string,
  success?: boolean,
): Promise<LogSearchResponse> {
  const params = new URLSearchParams({
    page: page.toString(),
    page_size: pageSize.toString(),
  });

  if (appName) {
    params.append("app_name", appName);
  }
  if (functionName) {
    params.append("function_name", functionName);
  }
  if (success !== undefined) {
    params.append("success", success.toString());
  }

  const response = await fetch(
    `${process.env.NEXT_PUBLIC_API_URL}/v1/logs/search?${params.toString()}`,
    {
      method: "GET",
      headers: {
        "X-API-KEY": apiKey,
      },
    },
  );

  if (!response.ok) {
    throw new Error(
      `Failed to fetch logs: ${response.status} ${response.statusText}`,
    );
  }

  return response.json();
}
