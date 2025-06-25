"use client";

import { ReactNode } from "react";
import { Skeleton } from "@/components/ui/skeleton";

interface LoadingGuardProps {
  children: ReactNode;
  isLoading?: boolean;
  loadingMessage?: string;
}

export const LoadingGuard = ({
  children,
  isLoading = false,
  loadingMessage = "Setting up your workspace...",
}: LoadingGuardProps) => {
  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen space-y-3">
        <h1 className="text-2xl font-semibold">{loadingMessage}</h1>
        <Skeleton className="h-[125px] w-[250px] rounded-xl" />
        <div className="space-y-2">
          <Skeleton className="h-4 w-[250px]" />
          <Skeleton className="h-4 w-[200px]" />
        </div>
      </div>
    );
  }

  return <>{children}</>;
};
