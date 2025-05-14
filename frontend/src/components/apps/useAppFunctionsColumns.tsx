"use client";

import { FunctionDetail } from "@/components/apps/function-detail";
import { type AppFunction } from "@/lib/types/appfunction";
import { useMemo } from "react";
import { IdDisplay } from "@/components/apps/id-display";
import { createColumnHelper, type ColumnDef } from "@tanstack/react-table";

const columnHelper = createColumnHelper<AppFunction>();

export const useAppFunctionsColumns = (): ColumnDef<AppFunction>[] => {
  return useMemo(() => {
    return [
      columnHelper.accessor("name", {
        header: "FUNCTION NAME",
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

      columnHelper.accessor("tags", {
        header: "TAGS",
        cell: (info) => (
          <div className="flex flex-wrap gap-2 overflow-hidden">
            {(info.getValue() || []).map((tag: string) => (
              <span
                key={tag}
                className="rounded-md bg-gray-100 px-3 py-1 text-sm font-medium text-gray-600 border border-gray-200"
              >
                {tag}
              </span>
            ))}
          </div>
        ),
        enableGlobalFilter: true,
        /** Set filterFn to "arrIncludes" for array filtering support */
        filterFn: "arrIncludes",
        enableColumnFilter: true,
      }),

      columnHelper.accessor("description", {
        header: "DESCRIPTION",
        cell: (info) => <div className="max-w-[500px]">{info.getValue()}</div>,
        enableGlobalFilter: true,
      }),

      columnHelper.accessor((row) => row, {
        id: "details",
        header: () => <div className="text-center">DETAILS</div>,
        cell: (info) => (
          <div className="text-center">
            <FunctionDetail func={info.getValue()} />
          </div>
        ),
        enableGlobalFilter: false,
      }),
    ] as ColumnDef<AppFunction>[];
  }, []);
};
