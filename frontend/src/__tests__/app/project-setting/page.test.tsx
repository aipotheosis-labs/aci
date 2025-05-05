import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import ProjectSettingPage from "@/app/project-setting/page";
import { useMetaInfo } from "@/components/context/metainfo";
import { getAllAppConfigs } from "@/lib/api/appconfig";
import { TooltipProvider } from "@/components/ui/tooltip";
import { OrgMemberInfoClass } from "@propelauth/react";

// Mock the modules
vi.mock("@/components/context/metainfo", () => ({
  useMetaInfo: vi.fn(),
}));
vi.mock("@/lib/api/app");
vi.mock("@/lib/api/appconfig");
vi.mock("@/lib/api/util", () => ({
  getApiKey: vi.fn(() => "test-api-key"),
}));

vi.mock("@/components/project/app-edit-form", () => ({
  AppEditForm: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="app-edit-form">{children}</div>
  ),
}));

vi.mock("@/components/project/agent-instruction-filter-form", () => ({
  AgentInstructionFilterForm: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="agent-instruction-form">{children}</div>
  ),
}));

const TestWrapper = ({ children }: { children: React.ReactNode }) => (
  <TooltipProvider>{children}</TooltipProvider>
);

describe("ProjectSettingPage", () => {
  const mockProject = {
    id: "project-123",
    name: "Test Project",
    owner_id: "owner-1",
    visibility_access: "private",
    daily_quota_used: 0,
    daily_quota_reset_at: "2024-01-01",
    total_quota_used: 0,
    created_at: "2024-01-01",
    updated_at: "2024-01-01",
    agents: [
      {
        id: "agent-1",
        name: "Test Agent",
        description: "Test Description",
        project_id: "project-123",
        allowed_apps: [],
        api_keys: [
          {
            id: "key-1",
            key: "test-key-1",
            agent_id: "agent-1",
            status: "active",
            created_at: "2024-01-01",
            updated_at: "2024-01-01",
          },
        ],
        created_at: "2024-01-01",
        updated_at: "2024-01-01",
        custom_instructions: {},
        excluded_apps: [],
        excluded_functions: [],
      },
    ],
  };

  beforeEach(() => {
    vi.clearAllMocks();

    // Mock MetaInfo context
    vi.mocked(useMetaInfo).mockReturnValue({
      activeProject: mockProject,
      accessToken: "test-token",
      reloadActiveProject: vi.fn(),
      setActiveProject: vi.fn(),
      orgs: [],
      activeOrg: {
        orgId: "org-123",
        orgName: "Test Org",
      } as OrgMemberInfoClass,
      setActiveOrg: vi.fn(),
      projects: [mockProject],
    });

    // Mock getAllAppConfigs
    vi.mocked(getAllAppConfigs).mockResolvedValue([
      {
        id: "config-1",
        project_id: "project-123",
        app_name: "TEST_APP_1",
        security_scheme: "none",
        security_scheme_overrides: {},
        enabled: true,
        all_functions_enabled: true,
        enabled_functions: [],
      },
    ]);
  });

  it("renders project settings when project is available", () => {
    render(<ProjectSettingPage />, { wrapper: TestWrapper });

    // Check if main title is rendered
    expect(screen.getByText("Project settings")).toBeInTheDocument();

    // Check if project name is displayed
    expect(screen.getByDisplayValue("Test Project")).toBeInTheDocument();

    // Check if project ID is displayed
    expect(screen.getByText("project-123")).toBeInTheDocument();
  });

  it("displays agent information correctly", async () => {
    render(<ProjectSettingPage />, { wrapper: TestWrapper });

    // Check if agent section is rendered
    const agentLabels = screen.getAllByText("Agent");
    expect(agentLabels[0]).toBeInTheDocument();

    const manageAgentsLabels = screen.getAllByText("Add and manage agents");
    expect(manageAgentsLabels[0]).toBeInTheDocument();

    // Check if agent table is rendered with correct data
    const agentNames = screen.getAllByDisplayValue("Test Agent");
    expect(agentNames[0]).toBeInTheDocument();

    const agentDescriptions = screen.getAllByDisplayValue("Test Description");
    expect(agentDescriptions[0]).toBeInTheDocument();
  });

  it("loads apps on component mount", async () => {
    render(<ProjectSettingPage />, { wrapper: TestWrapper });
    await waitFor(() => {
      expect(getAllAppConfigs).toHaveBeenCalledWith("test-api-key");
    });
  });
});
