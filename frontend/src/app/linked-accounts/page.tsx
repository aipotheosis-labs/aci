"use client";

import { useEffect, useState, useCallback, useMemo } from "react";
import { LinkedAccount } from "@/lib/types/linkedaccount";
import { Button } from "@/components/ui/button";
import { IdDisplay } from "@/components/apps/id-display";
import { GoTrash } from "react-icons/go";
import { Tabs, TabsContent } from "@/components/ui/tabs";
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
import { AddAccountForm } from "@/components/appconfig/add-account";
import { App } from "@/lib/types/app";
import { EnhancedSwitch } from "@/components/ui-extensions/enhanced-switch/enhanced-switch";
import Image from "next/image";
import { useMetaInfo } from "@/components/context/metainfo";
import { formatToLocalTime } from "@/utils/time";
import { ArrowUpDown } from "lucide-react";
import { EnhancedDataTable } from "@/components/ui-extensions/enhanced-data-table/data-table";
import { createColumnHelper, type ColumnDef } from "@tanstack/react-table";
import {
  useLinkedAccounts,
  useDeleteLinkedAccount,
  useUpdateLinkedAccount,
} from "@/hooks/use-linked-account";
import { useApps } from "@/hooks/use-app";
import { useAppConfigs } from "@/hooks/use-app-config";

const columnHelper = createColumnHelper<TableData>();
type TableData = LinkedAccount & { logo: string };

export default function LinkedAccountsPage() {
  const { activeProject } = useMetaInfo();
  const { data: linkedAccounts = [], isPending: isLinkedAccountsPending } =
    useLinkedAccounts();
  const { data: appConfigs = [], isPending: isConfigsPending } =
    useAppConfigs();
  const { data: apps, isPending: isAppsPending, isError } = useApps();
  const { mutateAsync: deleteLinkedAccount } = useDeleteLinkedAccount();
  const { mutateAsync: updateLinkedAccount } = useUpdateLinkedAccount();
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

  const toggleAccountStatus = useCallback(
    async (accountId: string, newStatus: boolean): Promise<boolean> => {
      try {
        await updateLinkedAccount({
          linkedAccountId: accountId,
          enabled: newStatus,
        });

        return true;
      } catch (error) {
        console.error("Failed to update linked account:", error);
        toast.error("Failed to update linked account");
        return false;
      }
    },
    [updateLinkedAccount],
  );

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
                        await deleteLinkedAccount({
                          linkedAccountId: account.id,
                        });

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
  }, [toggleAccountStatus, deleteLinkedAccount, activeProject]);

  const isPageLoading =
    isLinkedAccountsPending || isAppsPending || isConfigsPending;

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
          {!isPageLoading && !isError && appConfigs.length > 0 && (
            <AddAccountForm
              appInfos={appConfigs.map((config) => ({
                name: config.app_name,
                logo: apps.find((app) => app.name === config.app_name)?.logo,
                supported_security_schemes:
                  apps.find((app) => app.name === config.app_name)
                    ?.supported_security_schemes || {},
              }))}
            />
          )}
        </div>
      </div>
      <Separator />

      <div className="m-4">
        <Tabs defaultValue={"linked"} className="w-full">
          <TabsContent value="linked">
            {isPageLoading ? (
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
                paginationOptions={{
                  initialPageIndex: 0,
                  initialPageSize: 15,
                }}
              />
            )}
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
