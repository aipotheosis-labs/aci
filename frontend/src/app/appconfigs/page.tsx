"use client";

// import { Button } from "@/components/ui/button";
import { useCallback, useEffect, useState } from "react";
// import { GoPlus } from "react-icons/go";
import { AppConfig } from "@/lib/types/appconfig";
import { Separator } from "@/components/ui/separator";
import { getApiKey } from "@/lib/api/util";
import { getAllAppConfigs } from "@/lib/api/appconfig";
import { App } from "@/lib/types/app";
import { getAppLinkedAccounts } from "@/lib/api/linkedaccount";
import { useMetaInfo } from "@/components/context/metainfo";
import { useAppConfigsTableColumns } from "@/components/appconfig/useAppConfigsTableColumns";
import { EnhancedDataTable } from "@/components/ui-extensions/enhanced-data-table/data-table";
import { useApps } from "@/hooks/use-app";
export default function AppConfigPage() {
  const [appConfigs, setAppConfigs] = useState<AppConfig[]>([]);
  const [appsMap, setAppsMap] = useState<Record<string, App>>({});
  const { data: apps } = useApps();
  const [linkedAccountsCountMap, setLinkedAccountsCountMap] = useState<
    Record<string, number>
  >({});
  const [isLoading, setIsLoading] = useState(true);

  const { activeProject } = useMetaInfo();

  const loadAllData = useCallback(async () => {
    if (!apps) {
      return;
    }

    try {
      const apiKey = getApiKey(activeProject);
      const configs = await getAllAppConfigs(apiKey);

      const appsMapData = apps.reduce(
        (acc, app) => {
          acc[app.name] = app;
          return acc;
        },
        {} as Record<string, App>,
      );

      const linkedAccountsData = await Promise.all(
        configs.map(async (config) => {
          const linkedAccounts = await getAppLinkedAccounts(
            config.app_name,
            apiKey,
          );
          return [config.app_name, linkedAccounts.length];
        }),
      );

      setAppsMap(appsMapData);
      setAppConfigs(configs);
      setLinkedAccountsCountMap(Object.fromEntries(linkedAccountsData));
    } finally {
      setIsLoading(false);
    }
  }, [activeProject, apps]);

  useEffect(() => {
    loadAllData();
  }, [loadAllData]);

  const appConfigsColumns = useAppConfigsTableColumns({
    linkedAccountsCountMap,
    appsMap,
    updateAppConfigs: loadAllData,
  });

  return (
    <div>
      <div className="m-4 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">App Configurations</h1>
        </div>
        {/* <Button className="bg-primary hover:bg-primary/90 text-white">
          <GoPlus />
          Add App
        </Button> */}
      </div>
      <Separator />

      <div className="m-4">
        {isLoading && (
          <div className="flex items-center justify-center p-8">
            <div className="flex flex-col items-center space-y-4">
              <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent"></div>
              <p className="text-sm text-gray-500">Loading...</p>
            </div>
          </div>
        )}
        {!isLoading && (
          <EnhancedDataTable
            data={appConfigs}
            columns={appConfigsColumns}
            defaultSorting={[{ id: "app_name", desc: false }]}
            searchBarProps={{
              placeholder: "Search by app name",
            }}
          />
        )}
      </div>
    </div>
  );
}
