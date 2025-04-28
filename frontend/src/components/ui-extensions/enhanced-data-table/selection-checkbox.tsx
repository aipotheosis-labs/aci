"use client";

import { Row, Table } from "@tanstack/react-table";
import { Checkbox } from "@/components/ui/checkbox";

interface SelectionCheckboxProps<TData> {
  type: "header" | "cell";
  table?: Table<TData>;
  row?: Row<TData>;
}

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
              ? `border-[#1CD1AF] bg-[#1CD1AF] text-white data-[state=checked]:bg-[#1CD1AF]`
              : isSomeSelected
                ? `border-[#1CD1AF] bg-[#1CD1AF] text-white data-[state=indeterminate]:bg-[#1CD1AF]`
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
              ? `border-[#1CD1AF] bg-[#1CD1AF] text-white data-[state=checked]:bg-[#1CD1AF]`
              : "border-gray-300"
          }
        />
      </div>
    );
  }

  return null;
}
