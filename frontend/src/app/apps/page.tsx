"use client";

import { AppGrid } from "@/components/apps/app-grid";
import { Separator } from "@/components/ui/separator";
import { useApps } from "@/hooks/use-app";
import { AlertCircle, Loader2 } from "lucide-react";

export default function AppStorePage() {
  // TODO: implement pagination once we have a lot of apps
  const { data: apps, isPending, isError } = useApps([]);

  return (
    <div>
      <div className="m-4">
        <h1 className="text-2xl font-bold">App Store</h1>
        <p className="text-sm text-muted-foreground">
          Browse and connect with your favorite apps and tools.
        </p>
      </div>
      <Separator />

      <div className="m-4">
        {isPending ? (
          <div className="flex justify-center items-center py-16">
            <Loader2 className="animate-spin h-10 w-10 text-gray-500" />
            Loading apps...
          </div>
        ) : isError ? (
          <div className="flex justify-center items-center py-16">
            <AlertCircle className="h-10 w-10 text-red-500" />
            Failed to load apps. Please try to refresh the page.
          </div>
        ) : (
          <AppGrid apps={apps} />
        )}
      </div>
    </div>
  );
}
