import {
  AppFunction,
  FunctionExecute,
  FunctionExecutionResult,
  FunctionsSearchParams,
} from "@/lib/types/appfunction";

export async function executeFunction(
  functionName: string,
  body: FunctionExecute,
  apiKey: string,
): Promise<FunctionExecutionResult> {
  const response = await fetch(
    `${process.env.NEXT_PUBLIC_API_URL}/v1/functions/${functionName}/execute`,
    {
      method: "POST",
      headers: {
        "X-API-KEY": apiKey,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    },
  );

  if (!response.ok) {
    return {
      success: false,
      data: {},
      error: (await response.json()).error,
    };
  }

  const result = await response.json();
  return result;
}

export async function searchFunctions(
  params: FunctionsSearchParams,
  apiKey: string,
): Promise<AppFunction[]> {
  const searchParams = new URLSearchParams();

  if (params.app_names?.length) {
    params.app_names.forEach((name) => searchParams.append("app_names", name));
  }
  if (params.intent) {
    searchParams.append("intent", params.intent);
  }
  if (params.allowed_apps_only) {
    searchParams.append("allowed_apps_only", "true");
  }
  if (params.format) {
    searchParams.append("format", params.format);
  }
  if (params.limit) {
    searchParams.append("limit", params.limit.toString());
  }
  if (params.offset) {
    searchParams.append("offset", params.offset.toString());
  }

  const response = await fetch(
    `${process.env.NEXT_PUBLIC_API_URL}/v1/functions/search?${searchParams.toString()}`,
    {
      method: "GET",
      headers: {
        "X-API-KEY": apiKey,
      },
    },
  );

  if (!response.ok) {
    throw new Error(
      `Failed to search functions: ${response.status} ${response.statusText}`,
    );
  }

  const functions = await response.json();
  return functions;
}
