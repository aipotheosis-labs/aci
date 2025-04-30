"use client";

import { useMemo } from "react";
import { IdDisplay } from "@/components/apps/id-display";
import { createColumnHelper, type ColumnDef } from "@tanstack/react-table";
import { Agent } from "@/lib/types/project";
import { Button } from "@/components/ui/button";
import { ArrowUpDown } from "lucide-react";

const columnHelper = createColumnHelper<Agent>();

export const useAgentColumns = (): ColumnDef<Agent>[] => {
  return useMemo(() => {
    const columns = [
      columnHelper.accessor("name", {
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
              Agent Name
              <ArrowUpDown className="h-4 w-4" />
            </Button>
          </div>
        ),
        cell: (info) => <IdDisplay id={info.getValue()} dim={false} />,
        enableGlobalFilter: true,
        id: "name",
      }),
      columnHelper.accessor("description", {
        header: () => "Description",
        cell: (info) => <div className="max-w-[500px]">{info.getValue()}</div>,
        enableGlobalFilter: true,
      }),
    ];

    return columns as ColumnDef<Agent>[];
  }, []);
};
