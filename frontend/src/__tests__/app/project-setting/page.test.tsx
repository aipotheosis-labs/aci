import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import ProjectSettingPage from "@/app/project-setting/page";
import { useMetaInfo } from "@/components/context/metainfo";
import { TooltipProvider } from "@/components/ui/tooltip";
import { OrgMemberInfoClass, UserClass } from "@propelauth/react";
import { useAppConfigs } from "@/hooks/use-app-config";
import type { QueryObserverResult } from "@tanstack/react-query";
import { AppConfig } from "@/lib/types/appconfig";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

vi.mock("next/navigation", () => ({
  useRouter: vi.fn(),
}));

// Mock the modules
vi.mock("@/components/context/metainfo", () => ({
  useMetaInfo: vi.fn(),
}));

// Mock hooks/use-app-config instead of directly mocking API calls
vi.mock("@/hooks/use-app-config", () => ({
  useAppConfigs: vi.fn(),
  useCreateAppConfig: vi.fn(() => ({
    mutateAsync: vi.fn(),
  })),
}));

// Mock hooks/use-agent
vi.mock("@/hooks/use-agent", () => ({
  useCreateAgent: vi.fn(() => ({
    mutateAsync: vi.fn(),
  })),
  useUpdateAgent: vi.fn(() => ({
    mutateAsync: vi.fn(),
  })),
  useDeleteAgent: vi.fn(() => ({
    mutateAsync: vi.fn(),
  })),
}));

vi.mock("@/lib/api/app");
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

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
    },
  },
});

const TestWrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>{children}</TooltipProvider>
  </QueryClientProvider>
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

    queryClient.clear();

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
      user: {
        userId: "user-123",
        email: "test@example.com",
        createdAt: 1653312000000,
        getOrgByName: vi.fn(),
        getUserProperty: vi.fn(),
        getProperty: vi.fn(),
        getMetadata: vi.fn(),
        pictureUrl: "",
        impersonatorUserId: "",
        hasRole: vi.fn(),
        hasPermission: vi.fn(),
        hasAnyPermission: vi.fn(),
      } as unknown as UserClass,
    });

    // Mock useAppConfigs hook with proper React Query return structure
    vi.mocked(useAppConfigs).mockReturnValue({
      data: [
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
      ],
      isPending: false,
      isLoading: false,
      isError: false,
      error: null,
      isSuccess: true,
      isRefetching: false,
      isLoadingError: false,
      isRefetchError: false,
      refetch: vi.fn(),
      fetchStatus: "idle",
      status: "success",
      isFetched: true,
      isFetchedAfterMount: true,
      isFetching: false,
      dataUpdatedAt: Date.now(),
      errorUpdatedAt: 0,
      failureCount: 0,
      failureReason: null,
      errorUpdateCount: 0,
    } as unknown as QueryObserverResult<AppConfig[], Error>);
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
});
