"use client";

import React, { useEffect, useState } from "react";
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
import { useApp } from "@/hooks/use-app";
import Image from "next/image";
import { ConfigureApp } from "@/components/apps/configure-app";
import { EnhancedDataTable } from "@/components/ui-extensions/enhanced-data-table/data-table";
import { useAppConfig } from "@/hooks/use-app-config";
import { Loader2 } from "lucide-react";

const AppPage = () => {
  const { appName } = useParams<{ appName: string }>();
  const [functions, setFunctions] = useState<AppFunction[]>([]);
  const { app } = useApp(appName);
  const { data: appConfig, isPending: isAppConfigLoading } =
    useAppConfig(appName);

  const columns = useAppFunctionsColumns();

  useEffect(() => {
    if (app) {
      setFunctions(app.functions);
    }
  }, [app]);

  return (
    <div>
      <div className="m-4 flex items-center justify-between">
        <div>
          {app && (
            <div className="flex flex-col gap-4">
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
              <div className="max-w-3xl text-sm text-muted-foreground">
                {app.description}
              </div>
            </div>
          )}
        </div>
        <div className="flex items-center gap-2">
          {app && (
            <ConfigureApp
              name={app.name}
              supported_security_schemes={app.supported_security_schemes ?? {}}
              logo={app.logo}
            >
              <Button
                className="bg-primary text-white hover:bg-primary/90"
                disabled={isAppConfigLoading || !!appConfig}
              >
                {isAppConfigLoading ? (
                  <div className="flex items-center gap-2">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Loading...
                  </div>
                ) : appConfig ? (
                  "Configured"
                ) : (
                  "Configure App"
                )}
              </Button>
            </ConfigureApp>
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
          paginationOptions={{
            initialPageIndex: 0,
            initialPageSize: 15,
          }}
        />
      </div>
    </div>
  );
};

export default AppPage;
