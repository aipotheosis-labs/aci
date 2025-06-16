import { NextRequest, NextResponse } from "next/server";

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  // TODO: Remove this once we have a proper auth system
  // Do not set  Telemetry API Test Project ID in production
  const isLocal = process.env.NEXT_PUBLIC_ENVIRONMENT === "local";
  const testProjectId = process.env.TELEMETRY_API_TEST_PROJECT_ID;
  if (isLocal && testProjectId) {
    searchParams.set("project_id", testProjectId);
  }
  const token = process.env.TELEMETRY_API_TOKEN;
  if (!token) {
    return NextResponse.json(
      { error: "API token not configured" },
      { status: 500 },
    );
  }

  try {
    const url = `${process.env.TELEMETRY_API_URL}/v1/telemetry/logs?${searchParams.toString()}`;
    // TODO: Add Propel auth to verify the permission to access the logs
    const response = await fetch(url, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    if (!response.ok) {
      throw new Error(
        `Failed to fetch logs: ${response.status} ${response.statusText}`,
      );
    }
    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Error fetching logs:", error);
    return NextResponse.json(
      { error: "Next.js Server Error" + (error as Error).message },
      { status: 500 },
    );
  }
}
