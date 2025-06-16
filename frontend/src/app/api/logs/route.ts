import { NextRequest, NextResponse } from "next/server";
import { getProjects } from "@/lib/api/project";

export async function GET(request: NextRequest) {
  // Use telemetry token for the actual logs API call
  const telemetryToken = process.env.TELEMETRY_API_TOKEN;
  if (!telemetryToken) {
    return NextResponse.json(
      { error: "API token not configured" },
      { status: 500 },
    );
  }
  // Get project_id from request params
  const searchParams = request.nextUrl.searchParams;
  const projectId = searchParams.get("project_id");
  if (!projectId) {
    return NextResponse.json({ error: "Missing project_id" }, { status: 400 });
  }

  // Get Propel auth token and org_id from request headers
  const propelAuthToken = request.headers.get("authorization")?.split(" ")[1];
  const orgId = request.headers.get("org_id");
  if (!orgId || !propelAuthToken) {
    return NextResponse.json(
      { error: "Missing org_id or propelAuthToken" },
      { status: 400 },
    );
  }

  // Do not set Telemetry API Test Project ID in production
  // This is just for local development
  // TODO: Remove this once we have a proper local development setup
  const isLocal = process.env.NEXT_PUBLIC_ENVIRONMENT === "local";
  const testProjectId = process.env.TELEMETRY_API_TEST_PROJECT_ID;
  if (isLocal && testProjectId) {
    searchParams.set("project_id", testProjectId);
  }

  // Verify organization ID and project ID exist and user has access
  try {
    const projects = await getProjects(propelAuthToken, orgId);
    const hasAccess = projects.some((p) => p.id === projectId);
    if (!hasAccess) {
      return NextResponse.json(
        { error: "User does not have access to this project" },
        { status: 403 },
      );
    }
  } catch (error) {
    console.error("Error verifying access:", error);
    return NextResponse.json(
      { error: "Failed to verify access" },
      { status: 500 },
    );
  }
  // Fetch logs from telemetry API
  try {
    const url = `${process.env.TELEMETRY_API_URL}/v1/telemetry/logs?${searchParams.toString()}`;
    const response = await fetch(url, {
      headers: {
        Authorization: `Bearer ${telemetryToken}`,
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
