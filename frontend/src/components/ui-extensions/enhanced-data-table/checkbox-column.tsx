"use client";

import { useMemo } from "react";
import { createColumnHelper, type ColumnDef } from "@tanstack/react-table";
import { SelectionCheckbox } from "@/components/ui-extensions/enhanced-data-table/selection-checkbox";

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
          <SelectionCheckbox type="header" table={table} />
        ),
        cell: ({ row }) => <SelectionCheckbox type="cell" row={row} />,
      }),
    ];
  }, [renderSelectionColumn]);
}
