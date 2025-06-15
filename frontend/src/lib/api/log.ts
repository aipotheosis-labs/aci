import { LogSearchResponse, LogSearchParams } from "@/lib/types/log";

export async function searchFunctionExecutionLogs(
  params: LogSearchParams = {},
): Promise<LogSearchResponse> {
  const queryParams = new URLSearchParams();

  // Add all non-undefined parameters to the query
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined) {
      queryParams.append(key, value.toString());
    }
  });

  const response = await fetch(`/api/logs?${queryParams.toString()}`, {
    method: "GET",
  });

  if (!response.ok) {
    throw new Error(
      `Failed to fetch logs: ${response.status} ${response.statusText}`,
    );
  }

  return response.json();
}
