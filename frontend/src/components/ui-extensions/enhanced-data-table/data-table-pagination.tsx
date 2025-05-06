import React, { useState, useEffect } from "react";
import { Table } from "@tanstack/react-table";
// import {
//   Select,
//   SelectContent,
//   SelectItem,
//   SelectTrigger,
//   SelectValue,
// } from "@/components/ui/select";
import {
  Pagination,
  PaginationContent,
  PaginationItem,
  PaginationLink,
  PaginationPrevious,
  PaginationNext,
} from "@/components/ui/pagination";
import { ChevronsLeft, ChevronsRight } from "lucide-react";
import { cn } from "@/lib/utils";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

export const PaginationFirst = ({
  className,
  ...props
}: React.ComponentProps<typeof PaginationLink>) => (
  <PaginationLink
    aria-label="Go to first page"
    size="icon"
    className={cn(className)}
    {...props}
  >
    <ChevronsLeft className="h-4 w-4" />
    <span className="sr-only">First</span>
  </PaginationLink>
);

export const PaginationLast = ({
  className,
  ...props
}: React.ComponentProps<typeof PaginationLink>) => (
  <PaginationLink
    aria-label="Go to last page"
    size="icon"
    className={cn(className)}
    {...props}
  >
    <ChevronsRight className="h-4 w-4" />
    <span className="sr-only">Last</span>
  </PaginationLink>
);

interface DataTablePaginationProps<TData> {
  table: Table<TData>;
}

export function DataTablePagination<TData>({
  table,
}: DataTablePaginationProps<TData>) {
  const pageCount = table.getPageCount();
  const [pageInput, setPageInput] = useState(
    table.getState().pagination.pageIndex + 1,
  );

  useEffect(() => {
    const currentPageIndex = table.getState().pagination.pageIndex;
    setPageInput(currentPageIndex + 1);
  }, [table]);

  const jumpToPage = () => {
    const idx = Math.min(Math.max(pageInput, 1), pageCount) - 1;
    table.setPageIndex(idx);
  };

  return (
    <div className="flex items-center justify-between px-2 py-4 ">
      <div className="flex items-center ">
        <Pagination className="mt-0 cursor-pointer">
          <PaginationContent>
            <PaginationItem>
              <PaginationFirst
                onClick={() => table.firstPage()}
                className={
                  !table.getCanPreviousPage()
                    ? "pointer-events-none opacity-50"
                    : ""
                }
              />
            </PaginationItem>
            <PaginationItem>
              <PaginationPrevious
                onClick={() => table.previousPage()}
                className={
                  !table.getCanPreviousPage()
                    ? "pointer-events-none opacity-50"
                    : ""
                }
              />
            </PaginationItem>

            <PaginationItem className="flex items-center px-2">
              <Input
                type="number"
                min={1}
                max={pageCount}
                value={pageInput}
                onChange={(e) => setPageInput(Number(e.target.value))}
                onKeyDown={(e) => e.key === "Enter" && jumpToPage()}
                className="w-14 text-center"
              />
              <Button
                size="sm"
                onClick={jumpToPage}
                className="ml-1 bg-primary text-white"
              >
                Go
              </Button>
            </PaginationItem>

            <PaginationItem>
              <PaginationNext
                onClick={() => table.nextPage()}
                className={
                  !table.getCanNextPage()
                    ? "pointer-events-none opacity-50"
                    : ""
                }
              />
            </PaginationItem>
            <PaginationItem>
              <PaginationLast
                onClick={() => table.lastPage()}
                className={
                  !table.getCanNextPage()
                    ? "pointer-events-none opacity-50"
                    : ""
                }
              />
            </PaginationItem>
          </PaginationContent>
        </Pagination>

        <div className="flex w-[100px] items-center justify-center text-sm font-medium">
          Page {table.getState().pagination.pageIndex + 1} of{" "}
          {table.getPageCount()}
        </div>
      </div>
    </div>
  );
}
