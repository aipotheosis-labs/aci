import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor, cleanup } from "@testing-library/react";
import AppStorePage from "@/app/apps/page";
import { useApps } from "@/hooks/use-app";
import { useAppLinkedAccounts } from "@/hooks/use-linked-account";
import { App } from "@/lib/types/app";
import { AppConfig } from "@/lib/types/appconfig";
import { UseQueryResult } from "@tanstack/react-query";
import { useAppConfigs } from "@/hooks/use-app-config";

// Mock the useApps hook
vi.mock("@/hooks/use-app", () => ({
  useApps: vi.fn(),
}));

// Mock the useAppLinkedAccounts hook
vi.mock("@/hooks/use-linked-account", () => ({
  useAppLinkedAccounts: vi.fn(),
}));

// Mock the useAppConfigs hook
vi.mock("@/hooks/use-app-config", () => ({
  useAppConfigs: vi.fn(),
}));

describe("AppStorePage", () => {
  beforeEach(() => {
    vi.clearAllMocks();

    // Mock useAppConfigs to return empty array by default
    vi.mocked(useAppConfigs).mockReturnValue({
      data: [],
      isPending: false,
      isError: false,
      refetch: vi.fn(),
      error: null,
    } as unknown as UseQueryResult<AppConfig[], Error>);
  });

  afterEach(() => {
    cleanup();
  });

  it("shows loading state initially", () => {
    // Mock loading state
    vi.mocked(useApps).mockReturnValue({
      data: undefined,
      isPending: true,
      isError: false,
      refetch: vi.fn(),
      error: null,
    } as unknown as UseQueryResult<App[], Error>);

    render(<AppStorePage />);

    expect(screen.getByText("Loading apps...")).toBeInTheDocument();
  });

  it("shows error state", () => {
    // Mock error state
    vi.mocked(useApps).mockReturnValue({
      data: undefined,
      isPending: false,
      isError: true,
      refetch: vi.fn(),
      error: new Error("Failed to fetch"),
    } as unknown as UseQueryResult<App[], Error>);

    render(<AppStorePage />);

    expect(
      screen.getByText("Failed to load apps. Please try to refresh the page."),
    ).toBeInTheDocument();
  });

  it("loads and displays apps successfully", async () => {
    // Mock successful data state
    const mockApps: App[] = [
      {
        id: "1",
        name: "TEST_APP_1",
        display_name: "Test App 1",
        provider: "test",
        version: "1.0.0",
        description: "Test description",
        categories: ["test"],
        logo: "/test.png",
        visibility: "public",
        active: true,
        supported_security_schemes: {
          oauth2: {
            scope: "test",
          },
        },
        created_at: "2024-01-01",
        updated_at: "2024-01-01",
        functions: [],
      },
    ];
    vi.mocked(useApps).mockReturnValue({
      data: mockApps,
      isPending: false,
      isError: false,
      refetch: vi.fn(),
      error: null,
    } as unknown as UseQueryResult<App[], Error>);

    vi.mocked(useAppLinkedAccounts).mockReturnValue({
      data: [
        {
          id: "1",
          app_name: "TEST_APP_1",
          project_id: "1",
          linked_account_owner_id: "1",
          security_scheme: "oauth2",
          enabled: true,
          created_at: "2024-01-01",
          updated_at: "2024-01-01",
          last_used_at: null,
        },
        {
          id: "2",
          app_name: "TEST_APP_1",
          project_id: "1",
          linked_account_owner_id: "1121",
          security_scheme: "oauth2",
          enabled: true,
          created_at: "2024-01-01",
          updated_at: "2024-01-01",
          last_used_at: null,
        },
      ],
      isPending: false,
      isError: false,
    } as unknown as ReturnType<typeof useAppLinkedAccounts>);

    render(<AppStorePage />);
    screen.logTestingPlaygroundURL();

    expect(screen.getByText("App Store")).toBeInTheDocument();
    expect(
      screen.getByText("Browse and connect with your favorite apps and tools."),
    ).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText("Test App 1")).toBeInTheDocument();
    });

    expect(useApps).toHaveBeenCalledWith([]);
  });
});
