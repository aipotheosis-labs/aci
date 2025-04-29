"use client";

import { useMemo } from "react";
import { createColumnHelper, type ColumnDef } from "@tanstack/react-table";
import { Checkbox } from "@/components/ui/checkbox";

export function useSelectionColumn<TData>({
  renderSelectionColumn = false,
}: {
  renderSelectionColumn: boolean;
}): ColumnDef<TData>[] {
  return useMemo(() => {
    if (!renderSelectionColumn) return [];

    const columnHelper = createColumnHelper<TData>();
    return [
      columnHelper.display({
        id: "select",
        header: ({ table }) => (
          <div className="flex items-center justify-center">
            <Checkbox
              checked={
                table.getIsAllPageRowsSelected() ||
                (table.getIsSomePageRowsSelected() && "indeterminate")
              }
              onCheckedChange={(value) => {
                table.toggleAllRowsSelected(Boolean(value));
              }}
              aria-label="Select all"
            />
          </div>
        ),
        cell: ({ row }) => (
          <div className="flex items-center justify-center">
            <Checkbox
              checked={row.getIsSelected()}
              onCheckedChange={(value) => {
                row.toggleSelected(Boolean(value));
              }}
            />
          </div>
        ),
      }),
    ];
  }, [renderSelectionColumn]);
}
