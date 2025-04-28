"use client";

import { useEffect, useState, useCallback, useMemo } from "react";
import { LinkedAccount } from "@/lib/types/linkedaccount";
import { Button } from "@/components/ui/button";
import { IdDisplay } from "@/components/apps/id-display";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { GoTrash } from "react-icons/go";
import { Tabs, TabsContent } from "@/components/ui/tabs";
import { getApiKey } from "@/lib/api/util";
import {
  getAllLinkedAccounts,
  deleteLinkedAccount,
  updateLinkedAccount,
} from "@/lib/api/linkedaccount";
import { getApps } from "@/lib/api/app";
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { App } from "@/lib/types/app";
import { EnhancedSwitch } from "@/components/ui-extensions/enhanced-switch/enhanced-switch";
import Image from "next/image";
import { useMetaInfo } from "@/components/context/metainfo";

export default function LinkedAccountsPage() {
  const { activeProject } = useMetaInfo();
  const [linkedAccounts, setLinkedAccounts] = useState<LinkedAccount[]>([]);
  const [appConfigs, setAppConfigs] = useState<AppConfig[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [selectedOwnerId, setSelectedOwnerId] = useState<string>("all");
  const [appsMap, setAppsMap] = useState<Record<string, App>>({});
  const ownerIds = useMemo(
    () => [
      "all",
      ...new Set(linkedAccounts.map((a) => a.linked_account_owner_id)),
    ],
    [linkedAccounts],
  );

  const filteredLinkedAccounts = useMemo(() => {
    if (selectedOwnerId === "all") {
      return linkedAccounts;
    }
    return linkedAccounts.filter(
      (account) => account.linked_account_owner_id === selectedOwnerId,
    );
  }, [linkedAccounts, selectedOwnerId]);

  const loadAppMaps = useCallback(async () => {
    if (linkedAccounts.length === 0) {
      return;
    }

    try {
      const apiKey = getApiKey(activeProject);
      const appNames = Array.from(
        new Set(linkedAccounts.map((account) => account.app_name)),
      );

      const apps = await getApps(appNames, apiKey);

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
    } catch (error) {
      console.error("Failed to load app data:", error);
    }
  }, [activeProject, linkedAccounts]);

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

  const toggleAccountStatus = async (
    accountId: string,
    newStatus: boolean,
  ): Promise<boolean> => {
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
  };

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
          {!isLoading && appConfigs.length > 0 && (
            <AddAccountForm
              appInfos={appConfigs.map((config) => ({
                name: config.app_name,
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
            <div className="flex items-center space-x-4 mb-6">
              <Select
                value={selectedOwnerId}
                onValueChange={setSelectedOwnerId}
              >
                <SelectTrigger className="w-[120px]">
                  <SelectValue placeholder="ALL" />
                </SelectTrigger>
                <SelectContent>
                  {ownerIds.map((id) => (
                    <SelectItem key={id} value={id}>
                      {id}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {isLoading ? (
              <div className="text-center p-8">Loading...</div>
            ) : filteredLinkedAccounts.length === 0 ? (
              <div className="text-center p-8 text-muted-foreground">
                No linked accounts found
              </div>
            ) : (
              <div className="rounded-md border">
                <Table>
                  <TableHeader className="bg-gray-100">
                    <TableRow>
                      <TableHead>APP NAME</TableHead>
                      <TableHead>LINKED ACCOUNT OWNER ID</TableHead>
                      <TableHead>CREATED AT</TableHead>
                      <TableHead>ENABLED</TableHead>
                      <TableHead>DETAILS</TableHead>
                      <TableHead></TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredLinkedAccounts.map((account) => (
                      <TableRow key={account.id}>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            {appsMap[account.app_name]?.logo && (
                              <div className="relative h-6 w-6 flex-shrink-0 overflow-hidden">
                                <Image
                                  src={appsMap[account.app_name].logo}
                                  alt={`${account.app_name} logo`}
                                  fill
                                  className="object-contain rounded-sm"
                                />
                              </div>
                            )}
                            <span className="font-medium">
                              {account.app_name}
                            </span>
                          </div>
                        </TableCell>

                        <TableCell>
                          <div className="flex-shrink-0">
                            <IdDisplay id={account.linked_account_owner_id} />
                          </div>
                        </TableCell>
                        <TableCell>
                          {new Date(account.created_at)
                            .toISOString()
                            .replace(/\.\d{3}Z$/, "")
                            .replace("T", " ")}
                        </TableCell>
                        <TableCell>
                          <EnhancedSwitch
                            checked={account.enabled}
                            onAsyncChange={(checked) =>
                              toggleAccountStatus(account.id, checked)
                            }
                            successMessage={(newState) => {
                              return `Linked account ${account.linked_account_owner_id} ${newState ? "enabled" : "disabled"}`;
                            }}
                            errorMessage="Failed to update linked account"
                          />
                        </TableCell>
                        <TableCell>
                          <LinkedAccountDetails
                            account={account}
                            toggleAccountStatus={toggleAccountStatus}
                          >
                            <Button variant="outline" size="sm">
                              See Details
                            </Button>
                          </LinkedAccountDetails>
                        </TableCell>
                        <TableCell>
                          <AlertDialog>
                            <AlertDialogTrigger asChild>
                              <Button
                                variant="ghost"
                                size="sm"
                                className="text-red-600"
                              >
                                <GoTrash />
                              </Button>
                            </AlertDialogTrigger>
                            <AlertDialogContent>
                              <AlertDialogHeader>
                                <AlertDialogTitle>
                                  Confirm Deletion?
                                </AlertDialogTitle>
                                <AlertDialogDescription>
                                  This action cannot be undone. This will
                                  permanently delete the linked account for
                                  owner ID &quot;
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

                                      await deleteLinkedAccount(
                                        account.id,
                                        apiKey,
                                      );

                                      refreshLinkedAccounts(true);

                                      toast.success(
                                        `Linked account ${account.linked_account_owner_id} deleted`,
                                      );
                                    } catch (error) {
                                      console.error(error);
                                      toast.error(
                                        "Failed to delete linked account",
                                      );
                                    }
                                  }}
                                >
                                  Delete
                                </AlertDialogAction>
                              </AlertDialogFooter>
                            </AlertDialogContent>
                          </AlertDialog>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
