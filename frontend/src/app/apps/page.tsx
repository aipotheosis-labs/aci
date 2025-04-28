"use client";

import { AppGrid } from "@/components/apps/app-grid";
import { Separator } from "@/components/ui/separator";
import { App } from "@/lib/types/app";
import { useEffect, useState } from "react";
import { getApiKey } from "@/lib/api/util";
import { getAllApps } from "@/lib/api/app";
import { useMetaInfo } from "@/components/context/metainfo";

export default function AppStorePage() {
  const { activeProject } = useMetaInfo();
  const [apps, setApps] = useState<App[]>([]);
  const [loading, setLoading] = useState(true);

  // TODO: implement pagination once we have a lot of apps
  useEffect(() => {
    async function loadApps() {
      setLoading(true);
      try {
        const apiKey = getApiKey(activeProject);
        const apps = await getAllApps(apiKey);

        setApps(apps);
      } catch (error) {
        console.error("Error fetching apps:", error);
      } finally {
        setLoading(false);
      }
    }
    loadApps();
  }, [activeProject]);

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
        <AppGrid apps={apps} loading={loading} />
      </div>
    </div>
  );
}
