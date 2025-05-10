"use client";

import React, { useCallback, useEffect, useState } from "react";
import { useAppFunctionsColumns } from "@/components/apps/useAppFunctionsColumns";
import { Separator } from "@/components/ui/separator";
import { useParams } from "next/navigation";
import { IdDisplay } from "@/components/apps/id-display";
import { Button } from "@/components/ui/button";
import { BsQuestionCircle } from "react-icons/bs";
import {
  Tooltip,
  TooltipTrigger,
  TooltipContent,
} from "@/components/ui/tooltip";
import { type AppFunction } from "@/lib/types/appfunction";
import { toast } from "sonner";
import { AppConfig } from "@/lib/types/appconfig";
import { getApiKey } from "@/lib/api/util";
import { useApp } from "@/hooks/use-app";
import {
  AppAlreadyConfiguredError,
  createAppConfig,
  getAppConfig,
} from "@/lib/api/appconfig";
import Image from "next/image";
import { ConfigureAppPopup } from "@/components/apps/configure-app-popup";
import { EnhancedDataTable } from "@/components/ui-extensions/enhanced-data-table/data-table";
import { useMetaInfo } from "@/components/context/metainfo";

const AppPage = () => {
  const { activeProject } = useMetaInfo();
  const { appName } = useParams<{ appName: string }>();
  const [functions, setFunctions] = useState<AppFunction[]>([]);
  const [appConfig, setAppConfig] = useState<AppConfig | null>(null);

  const { app } = useApp(appName);

  const columns = useAppFunctionsColumns();

  useEffect(() => {
    if (app) {
      setFunctions(app.functions);
    }
  }, [app]);

  const loadAppConfig = useCallback(async () => {
    // TODO: replace with TanStack Query
    const apiKey = getApiKey(activeProject);
    const appConfig = await getAppConfig(appName, apiKey);
    setAppConfig(appConfig);
  }, [activeProject, appName]);

  useEffect(() => {
    async function loadData() {
      try {
        await loadAppConfig();
      } catch (error) {
        console.error("Error fetching app data:", error);
      }
    }

    loadData();
  }, [loadAppConfig]);

  const configureApp = async (security_scheme: string) => {
    const apiKey = getApiKey(activeProject);
    if (!app) return false;

    try {
      const appConfig = await createAppConfig(appName, security_scheme, apiKey);
      setAppConfig(appConfig);
      toast.success(`Successfully configured app: ${app.display_name}`);
      return true;
    } catch (error) {
      if (error instanceof AppAlreadyConfiguredError) {
        toast.error(
          `App configuration already exists for app: ${app.display_name}`,
        );
      } else {
        console.error("Error configuring app:", error);
        toast.error(`Failed to configure app. Please try again.`);
      }
      return false;
    }
  };

  return (
    <div>
      <div className="m-4 flex items-center justify-between">
        <div>
          {app && (
            <div className="flex items-center gap-4">
              <div className="relative h-12 w-12 flex-shrink-0 overflow-hidden rounded-lg">
                <Image
                  src={app?.logo ?? ""}
                  alt={`${app?.display_name} logo`}
                  fill
                  className="object-contain"
                />
              </div>
              <div>
                <h1 className="text-2xl font-bold">{app.display_name}</h1>
                <IdDisplay id={app.name} />
              </div>
            </div>
          )}
        </div>
        <div className="flex items-center gap-2">
          {app && (
            <ConfigureAppPopup
              name={app.name}
              security_schemes={app.security_schemes}
              configureApp={configureApp}
              logo={app.logo}
            >
              <Button
                className="bg-primary text-white hover:bg-primary/90"
                disabled={appConfig !== null}
              >
                {appConfig ? "Configured" : "Configure App"}
              </Button>
            </ConfigureAppPopup>
          )}
          <Tooltip>
            <TooltipTrigger asChild>
              <span className="cursor-pointer">
                <BsQuestionCircle className="h-4 w-4 text-muted-foreground" />
              </span>
            </TooltipTrigger>
            <TooltipContent side="top">
              <p className="text-xs">
                {appConfig
                  ? "The app has already been configured. It is ready for your agents to use."
                  : "Click to configure the application. This will add the application to your project, allowing your agents to use it."}
              </p>
            </TooltipContent>
          </Tooltip>
        </div>
      </div>
      <Separator />

      <div className="m-4">
        <EnhancedDataTable
          columns={columns}
          data={functions}
          searchBarProps={{ placeholder: "Search functions..." }}
        />
      </div>
    </div>
  );
};

export default AppPage;
