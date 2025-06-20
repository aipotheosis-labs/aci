import { LogSearchResponse, LogSearchParams } from "@/lib/types/log";

export async function searchFunctionExecutionLogs(
  params: LogSearchParams = {},
  orgId?: string,
  accessToken?: string,
): Promise<LogSearchResponse> {
  const queryParams = new URLSearchParams();
  if (!orgId || !accessToken) {
    throw new Error("orgId and accessToken are required");
  }

  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined) {
      queryParams.set(key, value.toString());
    }
  }

  const response = await fetch(`/api/logs?${queryParams.toString()}`, {
    method: "GET",
    headers: {
      ...(accessToken && { Authorization: `Bearer ${accessToken}` }),
      ...(orgId && { org_id: orgId }),
    },
  });

  if (!response.ok) {
    throw new Error(
      `Failed to fetch logs: ${response.status} ${response.statusText}`,
    );
  }

  return response.json();
}
