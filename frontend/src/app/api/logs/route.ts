import { NextRequest, NextResponse } from "next/server";

export async function GET(request: NextRequest) {
  const isLocal = process.env.NEXT_PUBLIC_ENVIRONMENT === "local";
  // TODO: Remove this once we have a proper auth system
  // Never set Telemetry API Test Project ID in production
  const testProjectId = process.env.TELEMETRY_API_TEST_PROJECT_ID;
  const searchParams = request.nextUrl.searchParams;
  console.log("isLocal", isLocal);
  console.log("testProjectId", testProjectId);
  if (isLocal && testProjectId) {
    console.log("Setting project_id to", testProjectId);
    searchParams.set("project_id", testProjectId);
  }
  const url = `${process.env.TELEMETRY_API_URL}/v1/telemetry/logs?${searchParams.toString()}`;
  try {
    // Get the authentication token from environment variables
    const token = process.env.TELEMETRY_API_TOKEN;
    if (!token) {
      return NextResponse.json(
        { error: "API token not configured" },
        { status: 500 },
      );
    }

    // Get search parameters from the URL

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
      { error: "Internal Server Error" },
      { status: 500 },
    );
  }
}
