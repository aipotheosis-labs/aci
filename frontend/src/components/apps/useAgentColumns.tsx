"use client";

import { useMemo } from "react";
import { IdDisplay } from "@/components/apps/id-display";
import { createColumnHelper, type ColumnDef } from "@tanstack/react-table";
import { Agent } from "@/lib/types/project";
import { Checkbox } from "@/components/ui/checkbox";

const columnHelper = createColumnHelper<Agent>();

export const useAgentColumns = (
  selectedAgentIds: Record<string, boolean>,
  toggleSelection: (agentId: string) => void,
): ColumnDef<Agent>[] => {
  return useMemo(() => {
    const columns = [
      columnHelper.display({
        id: "select",
        header: "",
        cell: ({ row }) => {
          const agent = row.original;
          const isSelected = agent.id ? !!selectedAgentIds[agent.id] : false;

          return (
            <div className="flex items-center justify-center">
              <Checkbox
                checked={isSelected}
                onCheckedChange={() => {
                  if (agent.id) {
                    toggleSelection(agent.id);
                  }
                }}
              />
            </div>
          );
        },
        size: 30,
      }),

      columnHelper.accessor("name", {
        header: "Agent Name",
        cell: (info) => <IdDisplay id={info.getValue()} dim={false} />,
        enableGlobalFilter: true,
        size: 50,
        /** Column ID needed for default sorting */
        id: "name",
        meta: {
          defaultSort: true,
          defaultSortDesc: true,
        },
      }),
      columnHelper.accessor("description", {
        header: "Description",
        cell: (info) => <div className="max-w-[500px]">{info.getValue()}</div>,
        enableGlobalFilter: true,
      }),
    ];

    return columns as ColumnDef<Agent>[];
  }, [selectedAgentIds, toggleSelection]);
};
