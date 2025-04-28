"use client";

import { Row, Table } from "@tanstack/react-table";
import { Checkbox } from "@/components/ui/checkbox";

interface SelectionCheckboxProps<TData> {
  type: "header" | "cell";
  table?: Table<TData>;
  row?: Row<TData>;
}

const PRIMARY_COLOR = "#1CD1AF";

export function SelectionCheckbox<TData>({
  type,
  table,
  row,
}: SelectionCheckboxProps<TData>) {
  if (type === "header" && table) {
    const isAllSelected = table.getIsAllRowsSelected();
    const isSomeSelected = table.getIsSomeRowsSelected();

    return (
      <div className="flex items-center justify-center">
        <Checkbox
          checked={isAllSelected}
          className={
            isAllSelected
              ? `border-[${PRIMARY_COLOR}] bg-[${PRIMARY_COLOR}] text-white data-[state=checked]:bg-[${PRIMARY_COLOR}]`
              : isSomeSelected
                ? `border-[${PRIMARY_COLOR}] bg-[${PRIMARY_COLOR}] text-white data-[state=indeterminate]:bg-[${PRIMARY_COLOR}]`
                : "border-gray-300"
          }
          data-state={
            isAllSelected
              ? "checked"
              : isSomeSelected
                ? "indeterminate"
                : "unchecked"
          }
          onCheckedChange={(value) => {
            table.toggleAllRowsSelected(Boolean(value));
          }}
        />
      </div>
    );
  }

  if (type === "cell" && row) {
    const isSelected = row.getIsSelected();

    return (
      <div className="flex items-center justify-center">
        <Checkbox
          checked={isSelected}
          onCheckedChange={(value) => {
            row.toggleSelected(Boolean(value));
          }}
          className={
            isSelected
              ? `border-[${PRIMARY_COLOR}] bg-[${PRIMARY_COLOR}] text-white data-[state=checked]:bg-[${PRIMARY_COLOR}]`
              : "border-gray-300"
          }
        />
      </div>
    );
  }

  return null;
}
