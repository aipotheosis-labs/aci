"use client";

import { useEffect, useState, useCallback, useMemo } from "react";
import { LinkedAccount } from "@/lib/types/linkedaccount";
import Image from "next/image";
import { Button } from "@/components/ui/button";
import { IdDisplay } from "@/components/apps/id-display";
import { LinkedAccountDetails } from "@/components/linkedaccount/linked-account-details";
import { BsQuestionCircle } from "react-icons/bs";
import {
  Tooltip,
  TooltipTrigger,
  TooltipContent,
} from "@/components/ui/tooltip";
import { GoTrash } from "react-icons/go";
import { useParams } from "next/navigation";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { App } from "@/lib/types/app";
import { AddAccountForm } from "@/components/appconfig/add-account";
import { getApiKey } from "@/lib/api/util";
import { getApp } from "@/lib/api/app";
import {
  getAppLinkedAccounts,
  deleteLinkedAccount,
  updateLinkedAccount,
} from "@/lib/api/linkedaccount";
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
import Link from "next/link";
import { EnhancedSwitch } from "@/components/ui-extensions/enhanced-switch/enhanced-switch";
import { useMetaInfo } from "@/components/context/metainfo";
import { formatToLocalTime } from "@/utils/time";
import { ArrowUpDown } from "lucide-react";
import { EnhancedDataTable } from "@/components/ui-extensions/enhanced-data-table/data-table";
import { createColumnHelper, type ColumnDef } from "@tanstack/react-table";

const columnHelper = createColumnHelper<LinkedAccount>();

export default function AppConfigDetailPage() {
  const { appName } = useParams<{ appName: string }>();
  const { activeProject } = useMetaInfo();
  const [app, setApp] = useState<App | null>(null);
  const [linkedAccounts, setLinkedAccounts] = useState<LinkedAccount[]>([]);

  const sortLinkedAccountsByCreateTime = (accounts: LinkedAccount[]) => {
    return [...accounts].sort((a, b) => {
      if (!a.created_at) return 1;
      if (!b.created_at) return -1;
      return (
        new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      );
    });
  };

  const refreshLinkedAccounts = useCallback(async () => {
    try {
      const apiKey = getApiKey(activeProject);
      const linkedAccounts = await getAppLinkedAccounts(appName, apiKey);
      setLinkedAccounts(sortLinkedAccountsByCreateTime(linkedAccounts));
    } catch (error) {
      console.error("Failed to refresh linked accounts:", error);
    }
  }, [activeProject, appName]);

  const toggleAccountStatus = useCallback(
    async (accountId: string, newStatus: boolean) => {
      try {
        const apiKey = getApiKey(activeProject);

        await updateLinkedAccount(accountId, apiKey, newStatus);

        // Refresh the linked accounts list after update
        await refreshLinkedAccounts();

        return true;
      } catch (error) {
        console.error("Failed to update linked account:", error);
        return false;
      }
    },
    [activeProject, refreshLinkedAccounts],
  );

  const handleDeleteLinkedAccount = useCallback(
    async (accountId: string, linkedAccountOwnerId: string) => {
      try {
        const apiKey = getApiKey(activeProject);
        await deleteLinkedAccount(accountId, apiKey);
        await refreshLinkedAccounts();

        toast.success(`Linked account ${linkedAccountOwnerId} deleted`);
      } catch (error) {
        console.error("Failed to delete linked account:", error);
        toast.error("Failed to delete linked account");
      }
    },
    [activeProject, refreshLinkedAccounts],
  );

  const linkedAccountsColumns: ColumnDef<LinkedAccount>[] = useMemo(() => {
    return [
      columnHelper.accessor("linked_account_owner_id", {
        header: ({ column }) => (
          <div className="flex items-center justify-start">
            <Button
              variant="ghost"
              onClick={() =>
                column.toggleSorting(column.getIsSorted() === "asc")
              }
              className="p-0 h-auto text-left font-normal bg-transparent hover:bg-transparent focus:ring-0"
            >
              LINKED ACCOUNT OWNER ID
              <ArrowUpDown className="ml-2 h-4 w-4" />
            </Button>
          </div>
        ),
        cell: (info) => (
          <div className="flex-shrink-0">
            <IdDisplay id={info.getValue()} />
          </div>
        ),
        enableGlobalFilter: true,
      }),

      columnHelper.accessor("created_at", {
        header: ({ column }) => (
          <div className="flex items-center justify-start">
            <Button
              variant="ghost"
              onClick={() =>
                column.toggleSorting(column.getIsSorted() === "asc")
              }
              className="p-0 h-auto text-left font-normal bg-transparent hover:bg-transparent focus:ring-0"
            >
              CREATED AT
              <ArrowUpDown className="ml-2 h-4 w-4" />
            </Button>
          </div>
        ),
        cell: (info) => formatToLocalTime(info.getValue()),
        enableGlobalFilter: false,
      }),

      columnHelper.accessor("last_used_at", {
        header: "LAST USED AT",
        cell: (info) => {
          const lastUsed = info.getValue();
          return lastUsed ? formatToLocalTime(lastUsed) : "Never";
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
                    onClick={() =>
                      handleDeleteLinkedAccount(
                        account.id,
                        account.linked_account_owner_id,
                      )
                    }
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
    ] as ColumnDef<LinkedAccount>[];
  }, [toggleAccountStatus, handleDeleteLinkedAccount]);

  useEffect(() => {
    async function loadAppAndLinkedAccounts() {
      try {
        const apiKey = getApiKey(activeProject);
        const app = await getApp(appName, apiKey);
        setApp(app);
        await refreshLinkedAccounts();
      } catch (error) {
        console.error("Failed to load app and linked accounts:", error);
      }
    }
    loadAppAndLinkedAccounts();
  }, [activeProject, appName, refreshLinkedAccounts]);

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <div className="relative h-12 w-12 flex-shrink-0 overflow-hidden rounded-lg">
            {app && (
              <Image
                src={app?.logo ?? ""}
                alt={`${app?.display_name} logo`}
                fill
                className="object-contain"
              />
            )}
          </div>
          <div>
            <Link href={`/apps/${app?.name}`}>
              <h1 className="text-2xl font-semibold">{app?.display_name}</h1>
            </Link>
            <IdDisplay id={app?.name ?? ""} />
          </div>
        </div>
        {app && (
          <AddAccountForm
            appInfos={[
              {
                name: app.name,
                logo: app.logo,
                securitySchemes: app.security_schemes,
              },
            ]}
            updateLinkedAccounts={refreshLinkedAccounts}
          />
        )}
      </div>

      <Tabs defaultValue={"linked"} className="w-full">
        <TabsList>
          <TabsTrigger value="linked">
            Linked Accounts
            <div className="ml-2">
              <Tooltip>
                <TooltipTrigger asChild>
                  <span className="cursor-pointer">
                    <BsQuestionCircle className="h-4 w-4 text-muted-foreground" />
                  </span>
                </TooltipTrigger>
                <TooltipContent side="top">
                  <p className="text-xs">
                    {
                      "This shows a list of end-users who have connected their account in this application to your agent."
                    }
                  </p>
                </TooltipContent>
              </Tooltip>
            </div>
          </TabsTrigger>
          {/* <TabsTrigger value="logs">Logs</TabsTrigger>
          <TabsTrigger value="settings">Settings</TabsTrigger> */}
        </TabsList>

        <TabsContent value="linked">
          <EnhancedDataTable
            data={linkedAccounts}
            columns={linkedAccountsColumns}
            defaultSorting={[{ id: "created_at", desc: true }]}
            searchBarProps={{
              placeholder: "Search by linked account owner ID",
            }}
          />
        </TabsContent>

        {/* <TabsContent value="logs">
          <div className="text-gray-500">Logs content coming soon...</div>
        </TabsContent>

        <TabsContent value="settings">
          <div className="text-gray-500">Settings content coming soon...</div>
        </TabsContent> */}
      </Tabs>
    </div>
  );
}
