"use client";

import { useState, useMemo } from "react";
import { LinkedAccount } from "@/lib/types/linkedaccount";
import { Button } from "@/components/ui/button";
import { IdDisplay } from "@/components/apps/id-display";
import { GoTrash } from "react-icons/go";
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
import { LinkedAccountDetails } from "@/components/linkedaccount/linked-account-details";
import { EnhancedSwitch } from "@/components/ui-extensions/enhanced-switch/enhanced-switch";
import Image from "next/image";
import { formatToLocalTime } from "@/utils/time";
import { ArrowUpDown, ChevronDown, ChevronRight } from "lucide-react";
import { EnhancedDataTable } from "@/components/ui-extensions/enhanced-data-table/data-table";
import { createColumnHelper, type ColumnDef } from "@tanstack/react-table";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { useDeleteLinkedAccount } from "@/hooks/use-linked-account";
import { useMetaInfo } from "@/components/context/metainfo";

const columnHelper = createColumnHelper<TableData>();
type TableData = LinkedAccount & { logo: string };

interface CollapsibleAccountGroupProps {
  ownerId: string;
  accounts: TableData[];
  toggleAccountStatus: (
    accountId: string,
    newStatus: boolean,
  ) => Promise<boolean>;
}

export function CollapsibleAccountGroup({
  ownerId,
  accounts,
  toggleAccountStatus,
}: CollapsibleAccountGroupProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const { mutateAsync: deleteLinkedAccount } = useDeleteLinkedAccount();
  const { activeProject } = useMetaInfo();

  const groupColumns: ColumnDef<TableData>[] = useMemo(() => {
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

  return (
    <Card className="mb-4">
      <CardHeader
        className="cursor-pointer hover:bg-gray-50 transition-colors"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {isExpanded ? (
              <ChevronDown className="h-4 w-4 text-gray-500" />
            ) : (
              <ChevronRight className="h-4 w-4 text-gray-500" />
            )}
            <div>
              <h3 className="text-lg font-semibold">
                Linked Accounts Owner ID
              </h3>
              <div className="mt-1">
                <IdDisplay id={ownerId} />
              </div>
            </div>
          </div>
          <div className="text-sm text-gray-500">
            {accounts.length} account{accounts.length !== 1 ? "s" : ""}
          </div>
        </div>
      </CardHeader>
      {isExpanded && (
        <CardContent className="pt-0">
          <EnhancedDataTable
            columns={groupColumns}
            data={accounts}
            defaultSorting={[{ id: "app_name", desc: false }]}
            searchBarProps={{
              placeholder: "Search APP NAME",
            }}
            paginationOptions={{
              initialPageIndex: 0,
              initialPageSize: 10,
            }}
          />
        </CardContent>
      )}
    </Card>
  );
}

export type { CollapsibleAccountGroupProps, TableData };
