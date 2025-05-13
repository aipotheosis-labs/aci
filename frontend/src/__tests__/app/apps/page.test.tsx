import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor, cleanup } from "@testing-library/react";
import AppStorePage from "@/app/apps/page";
import { useApps } from "@/hooks/use-app";
import { App } from "@/lib/types/app";
import { UseQueryResult } from "@tanstack/react-query";

// Mock the useApps hook
vi.mock("@/hooks/use-app", () => ({
  useApps: vi.fn(),
}));

describe("AppStorePage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
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
