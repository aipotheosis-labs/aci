"use client";

import { useState, useMemo } from "react";
import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Eye,
  ArrowUpDown,
  RefreshCw,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { createColumnHelper, type ColumnDef } from "@tanstack/react-table";
import { EnhancedDataTable } from "@/components/ui-extensions/enhanced-data-table/data-table";
import { useQuery } from "@tanstack/react-query";
import { searchFunctionExecutionLogs } from "@/lib/api/log";
import { useMetaInfo } from "@/components/context/metainfo";
import { LogEntry, LogSearchResponse } from "@/lib/types/log";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

const PAGE_SIZE = 10;

const columnHelper = createColumnHelper<LogEntry>();

// Custom hook for table data and operations
const useLogsTable = () => {
  const [selectedLogEntry, setSelectedLogEntry] = useState<LogEntry | null>(
    null,
  );
  const [isDetailPanelOpen, setIsDetailPanelOpen] = useState(false);
  const [nextPageCursor, setNextPageCursor] = useState<string | null>(null);
  const [cursorHistory, setCursorHistory] = useState<string[]>([]);
  const [currentPageNumber, setCurrentPageNumber] = useState(0);
  const pageSize = PAGE_SIZE;

  const { activeProject, accessToken, activeOrg } = useMetaInfo();

  const { data, isLoading, error, refetch } = useQuery<LogSearchResponse>({
    queryKey: ["logs", nextPageCursor],
    queryFn: () => {
      // Calculate start time as 3 days ago
      // TODO: Make this configurable, for enterprise customers
      // We support more than 3 days log retention
      const threeDaysAgo = new Date();
      threeDaysAgo.setDate(threeDaysAgo.getDate() - 3);

      return searchFunctionExecutionLogs(
        {
          log_type: "function_execution",
          limit: pageSize,
          start_time: threeDaysAgo.toISOString(),
          ...(nextPageCursor && { cursor: nextPageCursor }),
          ...(activeProject && { project_id: activeProject.id }),
        },
        activeOrg?.orgId,
        accessToken,
      );
    },
    refetchOnWindowFocus: false,
  });

  const getJsonPreview = (jsonString: string | null) => {
    if (!jsonString) return "";
    if (jsonString.length < 12) return jsonString;
    return jsonString.slice(0, 12) + "...";
  };

  const formatJson = (jsonString: string | null) => {
    if (!jsonString) return "";
    try {
      const parsedJson = JSON.parse(jsonString);
      return JSON.stringify(parsedJson, null, 2);
    } catch {
      return jsonString;
    }
  };

  const loadNextPage = () => {
    if (data?.cursor) {
      setCursorHistory((prev) => [...prev, nextPageCursor || ""]);
      setNextPageCursor(data.cursor);
      setCurrentPageNumber((prev) => prev + 1);
    }
  };

  const goToPreviousPage = () => {
    if (cursorHistory.length > 0) {
      const previousCursor = cursorHistory[cursorHistory.length - 1];
      setCursorHistory((prev) => prev.slice(0, -1));
      setNextPageCursor(previousCursor);
      setCurrentPageNumber((prev) => prev - 1);
    }
  };

  return {
    logs: data?.logs || [],
    totalCount: data?.total_count || 0,
    isLoading,
    error,
    selectedLogEntry,
    setSelectedLogEntry,
    isDetailPanelOpen,
    setIsDetailPanelOpen,
    getJsonPreview,
    formatJson,
    loadNextPage,
    goToPreviousPage,
    canGoBack: cursorHistory.length > 0,
    refetch,
    currentPageNumber,
  };
};

// Table columns definition
const useTableColumns = (
  setSelectedLogEntry: (log: LogEntry) => void,
  setIsDetailPanelOpen: (isOpen: boolean) => void,
  getJsonPreview: (jsonString: string | null) => string,
) => {
  return useMemo(() => {
    return [
      columnHelper.accessor("@timestamp", {
        header: ({ column }) => (
          <div className="flex items-center justify-start">
            <Button
              variant="ghost"
              onClick={() =>
                column.toggleSorting(column.getIsSorted() === "asc")
              }
              className="p-0 h-auto text-left font-normal bg-transparent hover:bg-transparent focus:ring-0"
            >
              TIMESTAMP
              <ArrowUpDown className="h-4 w-4" />
            </Button>
          </div>
        ),
        cell: (info) => info.getValue(),
        enableGlobalFilter: true,
      }),
      columnHelper.accessor("function_execution.app_name", {
        header: ({ column }) => (
          <div className="flex items-center justify-start">
            <Button
              variant="ghost"
              onClick={() =>
                column.toggleSorting(column.getIsSorted() === "asc")
              }
              className="p-0 h-auto text-left font-normal bg-transparent hover:bg-transparent focus:ring-0"
            >
              APP
              <ArrowUpDown className="h-4 w-4" />
            </Button>
          </div>
        ),
        cell: (info) => info.getValue() || "-",
        enableGlobalFilter: true,
      }),
      columnHelper.accessor("function_execution.function_name", {
        header: ({ column }) => (
          <div className="flex items-center justify-start">
            <Button
              variant="ghost"
              onClick={() =>
                column.toggleSorting(column.getIsSorted() === "asc")
              }
              className="p-0 h-auto text-left font-normal bg-transparent hover:bg-transparent focus:ring-0"
            >
              FUNCTION
              <ArrowUpDown className="h-4 w-4" />
            </Button>
          </div>
        ),
        cell: (info) => info.getValue() || "-",
        enableGlobalFilter: true,
      }),
      columnHelper.accessor(
        "function_execution.function_execution_result_success",
        {
          header: "STATUS",
          cell: (info) => {
            const success = info.getValue();
            const statusColor = success
              ? `bg-green-100 text-green-800`
              : `bg-red-100 text-red-800`;

            return (
              <div className="flex items-center">
                <span
                  className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${statusColor}`}
                >
                  {success ? "success" : "fail"}
                </span>
              </div>
            );
          },
          enableGlobalFilter: true,
        },
      ),
      columnHelper.accessor("function_execution.function_input", {
        header: "INPUT",
        cell: (info) => {
          const value = info.getValue();
          const preview = getJsonPreview(value);
          if (!preview) return "-";
          return (
            <div className="flex items-center">
              <span className="truncate max-w-[200px]">{preview}</span>
            </div>
          );
        },
        enableGlobalFilter: true,
      }),
      columnHelper.accessor(
        "function_execution.function_execution_result_data",
        {
          header: "OUTPUT",
          cell: (info) => {
            const value = info.getValue();
            const preview = getJsonPreview(value);
            if (!preview) return "-";
            return (
              <div className="flex items-center">
                <span className="truncate max-w-[200px]">{preview}</span>
              </div>
            );
          },
          enableGlobalFilter: true,
        },
      ),
      columnHelper.accessor((row) => row, {
        id: "actions",
        header: "",
        cell: (info) => {
          const log = info.getValue();
          return (
            <Button
              variant="ghost"
              size="icon"
              onClick={() => {
                setSelectedLogEntry(log);
                setIsDetailPanelOpen(true);
              }}
            >
              <Eye className="h-4 w-4" />
            </Button>
          );
        },
        enableGlobalFilter: false,
      }),
    ] as ColumnDef<LogEntry>[];
  }, [setSelectedLogEntry, setIsDetailPanelOpen, getJsonPreview]);
};

// Table view component
const LogsTableView = ({
  logs,
  columns,
  isLoading,
  totalCount,
  canGoBack,
  onLoadMore,
  onGoToPreviousPage,
  onRefresh,
  currentPageNumber,
}: {
  logs: LogEntry[];
  columns: ColumnDef<LogEntry>[];
  isLoading: boolean;
  totalCount: number;
  canGoBack: boolean;
  onLoadMore: () => void;
  onGoToPreviousPage: () => void;
  onRefresh: () => void;
  currentPageNumber: number;
}) => {
  if (isLoading && logs.length === 0) {
    return (
      <div className="flex items-center justify-center h-[400px]">
        <div className="text-center space-y-2">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
          <p className="text-muted-foreground">Loading logs...</p>
        </div>
      </div>
    );
  }

  if (logs.length === 0) {
    return (
      <div className="flex items-center justify-center h-[400px]">
        <div className="text-center space-y-2">
          <p className="text-muted-foreground">No logs found</p>
          <Button
            onClick={onRefresh}
            variant="default"
            size="sm"
            className="gap-2"
          >
            <RefreshCw className="h-4 w-4" />
            Refresh
          </Button>
        </div>
      </div>
    );
  }

  const startRow = currentPageNumber * PAGE_SIZE + 1;
  const endRow = Math.min(startRow + logs.length - 1, totalCount);

  return (
    <div className="rounded-md p-4">
      <div className="flex justify-between items-center mb-4">
        <p className="text-sm text-muted-foreground">
          Showing {startRow} – {endRow} of {totalCount} logs
        </p>
        <Button
          onClick={onRefresh}
          variant="default"
          size="sm"
          className="gap-2"
        >
          <RefreshCw className="h-4 w-4" />
          Refresh
        </Button>
      </div>
      <div className="overflow-x-auto w-full">
        <EnhancedDataTable
          columns={columns}
          data={logs}
          defaultSorting={[{ id: "@timestamp", desc: true }]}
        />
      </div>
      {totalCount > PAGE_SIZE && (
        <div className="flex justify-end items-center mt-4">
          <div className="flex items-center gap-2">
            <Button
              onClick={onGoToPreviousPage}
              variant="outline"
              size="sm"
              className="gap-2"
              disabled={!canGoBack || isLoading}
            >
              <ChevronLeft className="h-4 w-4" />
              Previous
            </Button>
            <Button
              onClick={onLoadMore}
              variant="outline"
              size="sm"
              className="gap-2"
              disabled={
                isLoading || logs.length < PAGE_SIZE || endRow >= totalCount
              }
            >
              Next
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};

// Log detail sheet component
const LogDetailSheet = ({
  selectedLogEntry,
  isDetailPanelOpen,
  setIsDetailPanelOpen,
  formatJson,
}: {
  selectedLogEntry: LogEntry | null;
  isDetailPanelOpen: boolean;
  setIsDetailPanelOpen: (isOpen: boolean) => void;
  formatJson: (jsonString: string | null) => string;
}) => {
  if (!selectedLogEntry) return null;

  return (
    <Sheet open={isDetailPanelOpen} onOpenChange={setIsDetailPanelOpen}>
      <SheetContent className="min-w-[600px] sm:min-w-[800px] max-w-[60vw]">
        <SheetHeader>
          <SheetTitle>Function Execution</SheetTitle>
        </SheetHeader>
        <ScrollArea className="h-[calc(100vh-8rem)] mt-6">
          <div className="space-y-6">
            <div>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-muted-foreground">App Name:</span>
                  <p className="break-all">
                    {selectedLogEntry.function_execution.app_name}
                  </p>
                </div>
                <div>
                  <span className="text-muted-foreground">Function Name:</span>
                  <p className="break-all">
                    {selectedLogEntry.function_execution.function_name}
                  </p>
                </div>
                <div>
                  <span className="text-muted-foreground">Start Time:</span>
                  <p className="break-all">
                    {
                      selectedLogEntry.function_execution
                        .function_execution_start_time
                    }
                  </p>
                </div>
                <div>
                  <span className="text-muted-foreground">End Time:</span>
                  <p className="break-all">
                    {
                      selectedLogEntry.function_execution
                        .function_execution_end_time
                    }
                  </p>
                </div>
                <div>
                  <span className="text-muted-foreground">Duration:</span>
                  <p className="break-all">
                    {selectedLogEntry.function_execution.function_execution_duration.toFixed(
                      3,
                    )}
                    s
                  </p>
                </div>
                <div>
                  <span className="text-muted-foreground">Status:</span>
                  <p>
                    <span
                      className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                        selectedLogEntry.function_execution
                          .function_execution_result_success
                          ? "bg-green-100 text-green-800"
                          : "bg-red-100 text-red-800"
                      }`}
                    >
                      {selectedLogEntry.function_execution
                        .function_execution_result_success
                        ? "success"
                        : "fail"}
                    </span>
                  </p>
                </div>
              </div>
            </div>

            <div>
              <h3 className="text-sm font-medium mb-2">Input</h3>
              <pre className="bg-muted p-4 rounded-lg overflow-auto text-sm whitespace-pre-wrap break-all">
                {formatJson(selectedLogEntry.function_execution.function_input)}
              </pre>
            </div>

            <div>
              <h3 className="text-sm font-medium mb-2">Output</h3>
              <pre className="bg-muted p-4 rounded-lg overflow-auto text-sm whitespace-pre-wrap break-all">
                {formatJson(
                  selectedLogEntry.function_execution
                    .function_execution_result_data,
                )}
              </pre>
            </div>

            {selectedLogEntry.function_execution
              .function_execution_result_error && (
              <div>
                <h3 className="text-sm font-medium mb-2">Error</h3>
                <pre className="bg-red-50 p-4 rounded-lg overflow-auto text-sm text-red-800 whitespace-pre-wrap break-all">
                  {
                    selectedLogEntry.function_execution
                      .function_execution_result_error
                  }
                </pre>
              </div>
            )}
          </div>
        </ScrollArea>
      </SheetContent>
    </Sheet>
  );
};

// Main page component
export default function LogsPage() {
  const {
    logs,
    totalCount,
    isLoading,
    selectedLogEntry,
    setSelectedLogEntry,
    isDetailPanelOpen,
    setIsDetailPanelOpen,
    getJsonPreview,
    formatJson,
    loadNextPage,
    goToPreviousPage,
    canGoBack,
    refetch,
    currentPageNumber,
  } = useLogsTable();

  const columns = useTableColumns(
    setSelectedLogEntry,
    setIsDetailPanelOpen,
    getJsonPreview,
  );

  return (
    <div className="container mx-auto">
      <Tabs defaultValue="function-executions" className="w-full pt-4">
        <TabsList className="px-2 ml-8 pl-2">
          <TabsTrigger value="function-executions">
            Function Executions
          </TabsTrigger>
        </TabsList>
        <TabsContent value="function-executions" className="px-4">
          <p className="mb-4 pl-4 text-sm text-muted-foreground">
            Showing function execution logs from the past 3 days
          </p>
          <p className="mb-4 pl-4 text-sm text-muted-foreground">
            We will support log retention more than 3 days (Coming soon), please
            see{" "}
            <a
              href="https://platform.aci.dev/pricing"
              className="text-blue-500"
            >
              https://platform.aci.dev/pricing
            </a>{" "}
            for more details.
          </p>
          <LogsTableView
            logs={logs}
            columns={columns}
            isLoading={isLoading}
            totalCount={totalCount}
            canGoBack={canGoBack}
            onLoadMore={loadNextPage}
            onGoToPreviousPage={goToPreviousPage}
            onRefresh={refetch}
            currentPageNumber={currentPageNumber}
          />
        </TabsContent>
      </Tabs>

      <LogDetailSheet
        selectedLogEntry={selectedLogEntry}
        isDetailPanelOpen={isDetailPanelOpen}
        setIsDetailPanelOpen={setIsDetailPanelOpen}
        formatJson={formatJson}
      />
    </div>
  );
}
