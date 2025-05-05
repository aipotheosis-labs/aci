"use client";

import { useEffect, useState, useCallback, useMemo } from "react";
import { LinkedAccount } from "@/lib/types/linkedaccount";
import { Button } from "@/components/ui/button";
import { IdDisplay } from "@/components/apps/id-display";
import { GoTrash } from "react-icons/go";
import { Tabs, TabsContent } from "@/components/ui/tabs";
import { getApiKey } from "@/lib/api/util";
import {
  getAllLinkedAccounts,
  deleteLinkedAccount,
  updateLinkedAccount,
} from "@/lib/api/linkedaccount";
import { getAllAppConfigs } from "@/lib/api/appconfig";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogDescription,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { toast } from "sonner";
import { Separator } from "@/components/ui/separator";
import { LinkedAccountDetails } from "@/components/linkedaccount/linked-account-details";
import { AppConfig } from "@/lib/types/appconfig";
import { AddAccountForm } from "@/components/appconfig/add-account";
import { App } from "@/lib/types/app";
import { EnhancedSwitch } from "@/components/ui-extensions/enhanced-switch/enhanced-switch";
import Image from "next/image";
import { useMetaInfo } from "@/components/context/metainfo";
import { formatToLocalTime } from "@/utils/time";
import { ArrowUpDown } from "lucide-react";
import { EnhancedDataTable } from "@/components/ui-extensions/enhanced-data-table/data-table";
import { createColumnHelper, type ColumnDef } from "@tanstack/react-table";
const columnHelper = createColumnHelper<TableData>();
import { useApps } from "@/hooks/use-app";

type TableData = LinkedAccount & { logo: string };

export default function LinkedAccountsPage() {
  const { activeProject } = useMetaInfo();
  const [linkedAccounts, setLinkedAccounts] = useState<LinkedAccount[]>([]);
  const [appConfigs, setAppConfigs] = useState<AppConfig[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const { data: apps, isPending, isError } = useApps();
  const [appsMap, setAppsMap] = useState<Record<string, App>>({});

  const loadAppMaps = useCallback(async () => {
    if (linkedAccounts.length === 0 || !apps) {
      return;
    }

    const appNames = Array.from(
      new Set(linkedAccounts.map((account) => account.app_name)),
    );

    const missingApps = appNames.filter(
      (name) => !apps.some((app) => app.name === name),
    );

    if (missingApps.length > 0) {
      console.warn(`Missing apps: ${missingApps.join(", ")}`);
    }

    setAppsMap(
      apps.reduce(
        (acc, app) => {
          acc[app.name] = app;
          return acc;
        },
        {} as Record<string, App>,
      ),
    );
  }, [linkedAccounts, apps]);

  /**
   * Generate tableData and attach the logo from appsMap to each row of data.
   * In this way, columns no longer need to rely on appsMap, avoiding uninstalling pop-up components when columns are rebuilt.
   */
  const tableData = useMemo(() => {
    return linkedAccounts.map((acc) => ({
      ...acc,
      logo: appsMap[acc.app_name]?.logo ?? "",
    }));
  }, [linkedAccounts, appsMap]);

  const loadAppConfigs = useCallback(async () => {
    try {
      setIsLoading(true);
      const apiKey = getApiKey(activeProject);
      const configs = await getAllAppConfigs(apiKey);
      setAppConfigs(configs);
    } catch (error) {
      console.error("Failed to load app configurations:", error);
      toast.error("Failed to load app configurations");
    } finally {
      setIsLoading(false);
    }
  }, [activeProject]);

  const refreshLinkedAccounts = useCallback(
    async (silent: boolean = false) => {
      try {
        if (!silent) {
          setIsLoading(true);
        }

        const apiKey = getApiKey(activeProject);
        const linkedAccounts = await getAllLinkedAccounts(apiKey);
        setLinkedAccounts(linkedAccounts);
      } catch (error) {
        console.error("Failed to load linked accounts:", error);
        toast.error("Failed to load linked accounts");
      } finally {
        if (!silent) {
          setIsLoading(false);
        }
      }
    },
    [activeProject],
  );

  const toggleAccountStatus = useCallback(
    async (accountId: string, newStatus: boolean): Promise<boolean> => {
      try {
        const apiKey = getApiKey(activeProject);

        await updateLinkedAccount(accountId, apiKey, newStatus);

        await refreshLinkedAccounts(true);

        return true;
      } catch (error) {
        console.error("Failed to update linked account:", error);
        toast.error("Failed to update linked account");
        return false;
      }
    },
    [activeProject, refreshLinkedAccounts],
  );

  useEffect(() => {
    const loadData = async () => {
      setIsLoading(true);
      await Promise.all([refreshLinkedAccounts(true), loadAppConfigs()]);
      setIsLoading(false);
    };

    loadData();
  }, [activeProject, loadAppConfigs, refreshLinkedAccounts]);

  useEffect(() => {
    if (linkedAccounts.length > 0) {
      loadAppMaps();
    }
  }, [linkedAccounts, loadAppMaps]);

  const linkedAccountsColumns: ColumnDef<TableData>[] = useMemo(() => {
    return [
      columnHelper.accessor("app_name", {
        header: ({ column }) => (
          <div className="flex items-center justify-start">
            <Button
              variant="ghost"
              onClick={() =>
                column.toggleSorting(column.getIsSorted() === "asc")
              }
              className="p-0 h-auto text-left font-normal bg-transparent hover:bg-transparent focus:ring-0"
            >
              APP NAME
              <ArrowUpDown className="h-4 w-4" />
            </Button>
          </div>
        ),
        cell: (info) => {
          const appName = info.getValue();
          return (
            <div className="flex items-center gap-2">
              {info.row.original.logo && (
                <div className="relative h-6 w-6 flex-shrink-0 overflow-hidden">
                  <Image
                    src={info.row.original.logo}
                    alt={`${appName} logo`}
                    fill
                    className="object-contain rounded-sm"
                  />
                </div>
              )}
              <span className="font-medium">{appName}</span>
            </div>
          );
        },
        enableGlobalFilter: true,
      }),

      columnHelper.accessor((row) => [row.linked_account_owner_id], {
        id: "linked_account_owner_id",
        header: ({ column }) => (
          <div className="flex items-center justify-start">
            <Button
              variant="ghost"
              onClick={() =>
                column.toggleSorting(column.getIsSorted() === "asc")
              }
              className="p-0 h-auto text-left font-normal  hover:bg-transparent focus:ring-0"
            >
              LINKED ACCOUNT OWNER ID
              <ArrowUpDown className="h-4 w-4" />
            </Button>
          </div>
        ),
        cell: (info) => {
          const [ownerId] = info.getValue();
          return (
            <div className="flex-shrink-0">
              <IdDisplay id={ownerId} />
            </div>
          );
        },
        enableColumnFilter: true,
        filterFn: "arrIncludes",
      }),

      columnHelper.accessor("created_at", {
        header: ({ column }) => (
          <div className="flex items-center justify-start">
            <Button
              variant="ghost"
              onClick={() =>
                column.toggleSorting(column.getIsSorted() === "asc")
              }
              className="p-0 h-auto text-left font-normal hover:bg-transparent focus:ring-0"
            >
              CREATED AT
              <ArrowUpDown className="h-4 w-4" />
            </Button>
          </div>
        ),
        cell: (info) => formatToLocalTime(info.getValue()),
        enableGlobalFilter: false,
      }),

      columnHelper.accessor("last_used_at", {
        header: "LAST USED AT",
        cell: (info) => {
          const lastUsedAt = info.getValue();
          return lastUsedAt ? formatToLocalTime(lastUsedAt) : "Never";
        },
        enableGlobalFilter: false,
      }),

      columnHelper.accessor("enabled", {
        header: "ENABLED",
        cell: (info) => {
          const account = info.row.original;
          return (
            <EnhancedSwitch
              checked={info.getValue()}
              onAsyncChange={(checked) =>
                toggleAccountStatus(account.id, checked)
              }
              successMessage={(newState) => {
                return `Linked account ${account.linked_account_owner_id} ${newState ? "enabled" : "disabled"}`;
              }}
              errorMessage="Failed to update linked account"
            />
          );
        },
        enableGlobalFilter: false,
      }),

      columnHelper.accessor((row) => row, {
        id: "details",
        header: "DETAILS",
        cell: (info) => {
          const account = info.getValue();
          return (
            <LinkedAccountDetails
              account={account}
              toggleAccountStatus={toggleAccountStatus}
            >
              <Button variant="outline" size="sm">
                See Details
              </Button>
            </LinkedAccountDetails>
          );
        },
        enableGlobalFilter: false,
      }),

      columnHelper.accessor((row) => row, {
        id: "actions",
        header: "",
        cell: (info) => {
          const account = info.getValue();
          return (
            <AlertDialog>
              <AlertDialogTrigger asChild>
                <Button variant="ghost" size="sm" className="text-red-600">
                  <GoTrash />
                </Button>
              </AlertDialogTrigger>
              <AlertDialogContent>
                <AlertDialogHeader>
                  <AlertDialogTitle>Confirm Deletion?</AlertDialogTitle>
                  <AlertDialogDescription>
                    This action cannot be undone. This will permanently delete
                    the linked account for owner ID &quot;
                    {account.linked_account_owner_id}&quot;.
                  </AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter>
                  <AlertDialogCancel>Cancel</AlertDialogCancel>
                  <AlertDialogAction
                    onClick={async () => {
                      try {
                        if (!activeProject) {
                          console.warn("No active project");
                          return;
                        }
                        const apiKey = getApiKey(activeProject);

                        await deleteLinkedAccount(account.id, apiKey);

                        refreshLinkedAccounts(true);

                        toast.success(
                          `Linked account ${account.linked_account_owner_id} deleted`,
                        );
                      } catch (error) {
                        console.error(error);
                        toast.error("Failed to delete linked account");
                      }
                    }}
                  >
                    Delete
                  </AlertDialogAction>
                </AlertDialogFooter>
              </AlertDialogContent>
            </AlertDialog>
          );
        },
        enableGlobalFilter: false,
      }),
    ] as ColumnDef<TableData>[];
  }, [toggleAccountStatus, refreshLinkedAccounts, activeProject]);

  return (
    <div>
      <div className="m-4 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Linked Accounts</h1>
          <p className="text-sm text-muted-foreground">
            Manage your linked accounts here.
          </p>
        </div>
        <div>
          {!isLoading && !isPending && !isError && appConfigs.length > 0 && (
            <AddAccountForm
              appInfos={appConfigs.map((config) => ({
                name: config.app_name,
                logo: apps.find((app) => app.name === config.app_name)?.logo,
                securitySchemes: [config.security_scheme],
              }))}
              updateLinkedAccounts={() => refreshLinkedAccounts(true)}
            />
          )}
        </div>
      </div>
      <Separator />

      <div className="m-4">
        <Tabs defaultValue={"linked"} className="w-full">
          <TabsContent value="linked">
            {isLoading ? (
              <div className="flex items-center justify-center p-8">
                <div className="flex flex-col items-center space-y-4">
                  <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent"></div>
                  <p className="text-sm text-gray-500">Loading...</p>
                </div>
              </div>
            ) : tableData.length === 0 ? (
              <div className="text-center p-8 text-muted-foreground">
                No linked accounts found
              </div>
            ) : (
              <EnhancedDataTable
                columns={linkedAccountsColumns}
                data={tableData}
                defaultSorting={[{ id: "app_name", desc: false }]}
                searchBarProps={{
                  placeholder: "Search linked accounts",
                }}
              />
            )}
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
