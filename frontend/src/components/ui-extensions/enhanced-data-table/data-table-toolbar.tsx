"use client";

import { Table } from "@tanstack/react-table";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { X } from "lucide-react";
import { useState } from "react";

interface EnhancedDataTableToolbarProps<TData> {
  table: Table<TData>;
  placeholder?: string;
  showSearchInput?: boolean;
  filterComponent?: React.ReactNode;
}

export function EnhancedDataTableToolbar<TData>({
  table,
  placeholder = "Search...",
  showSearchInput,
  filterComponent,
}: EnhancedDataTableToolbarProps<TData>) {
  const [searchValue, setSearchValue] = useState("");

  const handleSearch = (value: string) => {
    setSearchValue(value);
    table.setGlobalFilter(value);
  };

  const isFiltered = table.getState().globalFilter ? true : false;

  // Don't render toolbar if there's no search input and no filter component
  if (!showSearchInput && !filterComponent) {
    return null;
  }

  return (
    <div className="flex items-center justify-between py-4">
      <div className="flex items-center gap-4">
        {showSearchInput && (
          <div className="flex items-center space-x-2">
            <Input
              placeholder={placeholder}
              value={searchValue}
              onChange={(event) => handleSearch(event.target.value)}
              className="h-8 w-[250px]"
            />
            {isFiltered && (
              <Button
                variant="ghost"
                onClick={() => handleSearch("")}
                className="h-8 px-2 lg:px-3"
              >
                Clear
                <X className="h-4 w-4" />
              </Button>
            )}
          </div>
        )}

        {filterComponent}
      </div>
    </div>
  );
}
