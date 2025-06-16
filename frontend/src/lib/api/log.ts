import { LogSearchResponse, LogSearchParams } from "@/lib/types/log";

export async function searchFunctionExecutionLogs(
  params: LogSearchParams = {},
): Promise<LogSearchResponse> {
  const queryParams = new URLSearchParams();

  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined) {
      queryParams.set(key, value.toString());
    }
  }

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
