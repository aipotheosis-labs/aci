"use client";

import { useEffect, useState, useCallback, useMemo } from "react";
import { IdDisplay } from "@/components/apps/id-display";
import { Tabs, TabsContent } from "@/components/ui/tabs";
import { toast } from "sonner";
import { Separator } from "@/components/ui/separator";
import { AddAccountForm } from "@/components/appconfig/add-account";
import { App } from "@/lib/types/app";
import { Input } from "@/components/ui/input";
import {
  useLinkedAccounts,
  useUpdateLinkedAccount,
} from "@/hooks/use-linked-account";
import { useApps } from "@/hooks/use-app";
import { useAppConfigs } from "@/hooks/use-app-config";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  CollapsibleAccountGroup,
  type TableData,
} from "@/components/linkedaccount/collapsible-account-group";

export default function LinkedAccountsPage() {
  const { data: linkedAccounts = [], isPending: isLinkedAccountsPending } =
    useLinkedAccounts();
  const { data: appConfigs = [], isPending: isConfigsPending } =
    useAppConfigs();
  const { data: apps, isPending: isAppsPending, isError } = useApps();
  const { mutateAsync: updateLinkedAccount } = useUpdateLinkedAccount();
  const [appsMap, setAppsMap] = useState<Record<string, App>>({});
  const [selectedOwnerId, setSelectedOwnerId] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState<string>("");

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
   */
  const tableData = useMemo(() => {
    return linkedAccounts.map((acc) => ({
      ...acc,
      logo: appsMap[acc.app_name]?.logo ?? "",
    }));
  }, [linkedAccounts, appsMap]);

  // Get unique owner IDs
  const uniqueOwnerIds = useMemo(() => {
    return Array.from(
      new Set(linkedAccounts.map((acc) => acc.linked_account_owner_id)),
    ).sort();
  }, [linkedAccounts]);

  // Group accounts by owner ID
  const groupedAccounts = useMemo(() => {
    const groups: Record<string, TableData[]> = {};
    tableData.forEach((account) => {
      if (!groups[account.linked_account_owner_id]) {
        groups[account.linked_account_owner_id] = [];
      }
      groups[account.linked_account_owner_id].push(account);
    });
    return groups;
  }, [tableData]);

  // Filter groups based on selection and search query
  const filteredGroups = useMemo(() => {
    let filteredBySelection = groupedAccounts;

    // Apply dropdown filter
    if (selectedOwnerId !== "all") {
      filteredBySelection =
        selectedOwnerId in groupedAccounts
          ? { [selectedOwnerId]: groupedAccounts[selectedOwnerId] }
          : {};
    }

    // Apply search filter
    if (searchQuery.trim()) {
      const filtered: Record<string, TableData[]> = {};
      Object.entries(filteredBySelection).forEach(([ownerId, accounts]) => {
        if (ownerId.toLowerCase().includes(searchQuery.toLowerCase())) {
          filtered[ownerId] = accounts;
        }
      });
      return filtered;
    }

    return filteredBySelection;
  }, [groupedAccounts, selectedOwnerId, searchQuery]);

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

      {/* Owner ID Filter and Search */}
      {!isPageLoading && uniqueOwnerIds.length > 0 && (
        <div className="m-4">
          <div className="flex items-center gap-4 mb-4 flex-wrap">
            <div className="flex items-center gap-4">
              <label className="text-sm font-medium">Filter by Owner ID:</label>
              <Select
                value={selectedOwnerId}
                onValueChange={setSelectedOwnerId}
              >
                <SelectTrigger className="w-64">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">
                    All Owner IDs ({uniqueOwnerIds.length})
                  </SelectItem>
                  {uniqueOwnerIds.map((ownerId) => (
                    <SelectItem key={ownerId} value={ownerId}>
                      <IdDisplay id={ownerId} />
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="flex items-center gap-4">
              <label className="text-sm font-medium">Search Owner ID:</label>
              <Input
                placeholder="Search owner IDs..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-64"
              />
              {searchQuery && (
                <span className="text-xs text-muted-foreground">
                  Found {Object.keys(filteredGroups).length} matching owner
                  {Object.keys(filteredGroups).length !== 1 ? "s" : ""}
                </span>
              )}
            </div>
          </div>
        </div>
      )}

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
            ) : Object.keys(filteredGroups).length === 0 ? (
              <div className="text-center p-8 text-muted-foreground">
                No linked accounts found
              </div>
            ) : (
              <div className="space-y-4">
                {Object.entries(filteredGroups).map(([ownerId, accounts]) => (
                  <CollapsibleAccountGroup
                    key={ownerId}
                    ownerId={ownerId}
                    accounts={accounts}
                    toggleAccountStatus={toggleAccountStatus}
                  />
                ))}
              </div>
            )}
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
