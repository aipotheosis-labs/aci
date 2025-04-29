import { AppConfig } from "@/lib/types/appconfig";
import { createColumnHelper, type ColumnDef } from "@tanstack/react-table";
import { useMemo } from "react";
import { Button } from "@/components/ui/button";
import { ArrowUpDown } from "lucide-react";
import { IdDisplay } from "@/components/apps/id-display";

const columnHelper = createColumnHelper<AppConfig>();

export const useAllowAppsColumns = (): ColumnDef<AppConfig>[] => {
  return useMemo(() => {
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
              className="w-full justify-start px-0"
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
};
