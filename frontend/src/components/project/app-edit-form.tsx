"use client";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogTrigger,
} from "@/components/ui/dialog";
import { useState, useEffect, useMemo } from "react";
import { Separator } from "@/components/ui/separator";
import { useUpdateAgent } from "@/hooks/use-agent";
import { toast } from "sonner";
import { Badge } from "@/components/ui/badge";
import { EnhancedDataTable } from "@/components/ui-extensions/enhanced-data-table/data-table";
import { RowSelectionState } from "@tanstack/react-table";
import { IdDisplay } from "@/components/apps/id-display";
import { createColumnHelper, type ColumnDef } from "@tanstack/react-table";
import { ArrowUpDown } from "lucide-react";
import { useAppConfigs } from "@/hooks/use-app-config";
import { AppConfig } from "@/lib/types/appconfig";

interface AppEditFormProps {
  children: React.ReactNode;
  agentId: string;
  allowedApps: string[];
}

export function AppEditForm({
  children,
  agentId,
  allowedApps,
}: AppEditFormProps) {
  const [open, setOpen] = useState(false);
  const [selectedApps, setSelectedApps] = useState<RowSelectionState>({});
  const { data: appConfigs = [], isPending: isConfigsPending } =
    useAppConfigs();

  const { mutateAsync: updateAgentMutation } = useUpdateAgent();
  const columns: ColumnDef<AppConfig>[] = useMemo(() => {
    const columnHelper = createColumnHelper<AppConfig>();
    return [
      columnHelper.accessor("app_name", {
        header: ({ column }) => (
          <div className="text-left">
            <Button
              variant="ghost"
              onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                column.toggleSorting(column.getIsSorted() === "asc");
              }}
              className="justify-start px-0"
              type="button"
            >
              App Name
              <ArrowUpDown className="h-4 w-4" />
            </Button>
          </div>
        ),
        cell: ({ row }) => <IdDisplay id={row.original.app_name} />,
        enableGlobalFilter: true,
        id: "app_name",
      }),
    ] as ColumnDef<AppConfig>[];
  }, []);
  const [submitLoading, setSubmitLoading] = useState(false);

  useEffect(() => {
    if (!open) return;

    const initialSelection: RowSelectionState = {};
    appConfigs.forEach((config: AppConfig) => {
      initialSelection[config.app_name] = allowedApps.includes(config.app_name);
    });
    setSelectedApps(initialSelection);
  }, [open, allowedApps, appConfigs]);

  const selectedAppNames = useMemo(
    () => Object.keys(selectedApps).filter((app) => selectedApps[app]),
    [selectedApps],
  );

  const handleSubmit = async () => {
    try {
      setSubmitLoading(true);
      await updateAgentMutation({
        id: agentId,
        data: {
          allowed_apps: selectedAppNames,
        },
      });
      toast.success("Agent's allowed apps have been updated successfully.");
    } catch (error) {
      console.error("Failed to update agent's allowed apps:", error);
      toast.error("Failed to update agent's allowed apps.");
    } finally {
      setSubmitLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>{children}</DialogTrigger>
      <DialogContent className="sm:max-w-[425px] ">
        <DialogHeader className="space-y-4">
          <div className="flex items-center justify-between">
            <DialogTitle>Edit Allowed Apps</DialogTitle>
          </div>
          <p className="text-sm text-gray-500 mt-2">
            Select what apps are enabled for this agent.
          </p>
          <Separator />
        </DialogHeader>

        <div className="space-y-4">
          <div className="space-y-2">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium">Allowed Apps</h3>
              <Badge
                variant="secondary"
                className="flex items-center gap-1 px-2 py-1 text-xs"
              >
                {Object.values(selectedApps).filter(Boolean).length} Selected
              </Badge>
            </div>
            {selectedAppNames.length > 0 && (
              <div className="max-w-[300px] truncate">
                <IdDisplay id={selectedAppNames.join(",")} />
              </div>
            )}

            {isConfigsPending ? (
              <div className="flex h-40  justify-center py-4 ">
                <p>Loading...</p>
              </div>
            ) : appConfigs.length === 0 ? (
              <div className="flex h-40  justify-center py-4">
                <p>No app configurations available</p>
              </div>
            ) : (
              <div className="max-h-[45vh] overflow-y-auto">
                <EnhancedDataTable
                  columns={columns}
                  data={appConfigs}
                  defaultSorting={[{ id: "app_name", desc: false }]}
                  searchBarProps={{ placeholder: "Search apps..." }}
                  rowSelectionProps={{
                    rowSelection: selectedApps,
                    onRowSelectionChange: setSelectedApps,
                    getRowId: (row) => row.app_name,
                  }}
                />
              </div>
            )}
          </div>

          <DialogFooter>
            <Button onClick={handleSubmit} disabled={submitLoading}>
              {submitLoading ? "Saving..." : "Save"}
            </Button>
          </DialogFooter>
        </div>
      </DialogContent>
    </Dialog>
  );
}
