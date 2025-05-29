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
import { Eye, ArrowUpDown, RefreshCw } from "lucide-react";
import { createColumnHelper, type ColumnDef } from "@tanstack/react-table";
import { EnhancedDataTable } from "@/components/ui-extensions/enhanced-data-table/data-table";
import { useQuery } from "@tanstack/react-query";
import { searchLogs } from "@/lib/api/logs";
import { useMetaInfo } from "@/components/context/metainfo";
import { getApiKey } from "@/lib/api/util";
import { LogEntry, LogSearchResponse } from "@/lib/types/logs";

// Configuration
export const LOGS_CONFIG = {
  refreshInterval: 30000, // 30 seconds
  maxLogsPerPage: 50,
  statusColors: {
    success: {
      bg: "bg-green-100",
      text: "text-green-800",
    },
    error: {
      bg: "bg-red-100",
      text: "text-red-800",
    },
    warning: {
      bg: "bg-yellow-100",
      text: "text-yellow-800",
    },
    info: {
      bg: "bg-blue-100",
      text: "text-blue-800",
    },
  },
} as const;

export type LogStatus = keyof typeof LOGS_CONFIG.statusColors;

const columnHelper = createColumnHelper<LogEntry>();

// Custom hook for table data and operations
const useLogsTable = () => {
  const [selectedLog, setSelectedLog] = useState<LogEntry | null>(null);
  const [isDetailOpen, setIsDetailOpen] = useState(false);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(5);

  const { activeProject } = useMetaInfo();
  const apiKey = getApiKey(activeProject);

  const { data, isLoading, error, refetch } = useQuery<LogSearchResponse>({
    queryKey: ["logs", page, pageSize],
    queryFn: () => searchLogs(apiKey, page, pageSize),
  });

  const getJsonPreview = (jsonStr: string | null) => {
    if (!jsonStr) return "";
    try {
      const obj = JSON.parse(jsonStr);
      const firstKey = Object.keys(obj)[0];
      const firstValue = obj[firstKey];
      return `${firstKey}: ${typeof firstValue === "string" ? firstValue : JSON.stringify(firstValue)}`;
    } catch {
      return jsonStr;
    }
  };

  const formatJson = (jsonStr: string | null) => {
    if (!jsonStr) return "";
    try {
      const obj = JSON.parse(jsonStr);
      return JSON.stringify(obj, null, 2);
    } catch {
      return jsonStr;
    }
  };

  return {
    logs: data?.logs || [],
    total: data?.total || 0,
    isLoading,
    error,
    selectedLog,
    setSelectedLog,
    isDetailOpen,
    setIsDetailOpen,
    getJsonPreview,
    formatJson,
    page,
    setPage,
    pageSize,
    setPageSize,
    refetch,
  };
};

// Table columns definition
const useTableColumns = (
  setSelectedLog: (log: LogEntry) => void,
  setIsDetailOpen: (isOpen: boolean) => void,
  getJsonPreview: (jsonStr: string | null) => string,
) => {
  return useMemo(() => {
    return [
      columnHelper.accessor("timestamp", {
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
      columnHelper.accessor("function_execution_app_name", {
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
      columnHelper.accessor("function_execution_function_name", {
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
      columnHelper.accessor("function_execution_input", {
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
      columnHelper.accessor("function_execution_result_data", {
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
      }),
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
                setSelectedLog(log);
                setIsDetailOpen(true);
              }}
            >
              <Eye className="h-4 w-4" />
            </Button>
          );
        },
        enableGlobalFilter: false,
      }),
    ] as ColumnDef<LogEntry>[];
  }, [setSelectedLog, setIsDetailOpen, getJsonPreview]);
};

// Table view component
const LogsTableView = ({
  logs,
  columns,
  isLoading,
  page,
  setPage,
  pageSize,
  setPageSize,
  total,
  onRefresh,
}: {
  logs: LogEntry[];
  columns: ColumnDef<LogEntry>[];
  isLoading: boolean;
  page: number;
  setPage: (page: number) => void;
  pageSize: number;
  setPageSize: (size: number) => void;
  total: number;
  onRefresh: () => void;
}) => {
  if (isLoading) {
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

  return (
    <div className="rounded-md p-4">
      <div className="flex justify-end mb-4">
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
          defaultSorting={[{ id: "timestamp", desc: true }]}
          searchBarProps={{
            placeholder: "Search logs",
          }}
          paginationOptions={{
            initialPageIndex: page - 1,
            initialPageSize: pageSize,
            totalCount: total,
            onPageChange: (newPage) => setPage(newPage + 1),
            onPageSizeChange: setPageSize,
          }}
        />
      </div>
    </div>
  );
};

// Log detail sheet component
const LogDetailSheet = ({
  selectedLog,
  isDetailOpen,
  setIsDetailOpen,
  formatJson,
}: {
  selectedLog: LogEntry | null;
  isDetailOpen: boolean;
  setIsDetailOpen: (isOpen: boolean) => void;
  formatJson: (jsonStr: string | null) => string;
}) => {
  if (!selectedLog) return null;

  const getStatusColor = (success: boolean | null) => {
    if (success === null) return LOGS_CONFIG.statusColors.info;
    return success
      ? LOGS_CONFIG.statusColors.success
      : LOGS_CONFIG.statusColors.error;
  };

  const statusColor = getStatusColor(
    selectedLog.function_execution_result_success,
  );

  return (
    <Sheet open={isDetailOpen} onOpenChange={setIsDetailOpen}>
      <SheetContent className="min-w-[600px] sm:min-w-[800px] max-w-[60vw]">
        <SheetHeader>
          <SheetTitle>Log Details</SheetTitle>
        </SheetHeader>
        <ScrollArea className="h-[calc(100vh-8rem)] mt-6">
          <div className="space-y-6">
            <div>
              <h3 className="text-sm font-medium mb-2">Basic Information</h3>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-muted-foreground">Timestamp:</span>
                  <p>{selectedLog.timestamp}</p>
                </div>
                <div>
                  <span className="text-muted-foreground">App Name:</span>
                  <p>{selectedLog.function_execution_app_name || "-"}</p>
                </div>
                <div>
                  <span className="text-muted-foreground">Function:</span>
                  <p>{selectedLog.function_execution_function_name || "-"}</p>
                </div>
                <div>
                  <span className="text-muted-foreground">Status:</span>
                  <p
                    className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${statusColor.bg} ${statusColor.text}`}
                  >
                    {selectedLog.function_execution_result_success
                      ? "success"
                      : "error"}
                  </p>
                </div>
              </div>
            </div>

            <div>
              <h3 className="text-sm font-medium mb-2">Input</h3>
              <pre className="bg-muted p-4 rounded-lg overflow-auto text-sm">
                {formatJson(selectedLog.function_execution_input)}
              </pre>
            </div>

            <div>
              <h3 className="text-sm font-medium mb-2">Output</h3>
              <pre className="bg-muted p-4 rounded-lg overflow-auto text-sm">
                {formatJson(selectedLog.function_execution_result_data)}
              </pre>
            </div>

            {selectedLog.function_execution_result_error && (
              <div>
                <h3 className="text-sm font-medium mb-2">Error</h3>
                <pre className="bg-red-50 p-4 rounded-lg overflow-auto text-sm text-red-800">
                  {selectedLog.function_execution_result_error}
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
    total,
    isLoading,
    selectedLog,
    setSelectedLog,
    isDetailOpen,
    setIsDetailOpen,
    getJsonPreview,
    formatJson,
    page,
    setPage,
    pageSize,
    setPageSize,
    refetch,
  } = useLogsTable();

  const columns = useTableColumns(
    setSelectedLog,
    setIsDetailOpen,
    getJsonPreview,
  );

  return (
    <div className="container mx-auto">
      <LogsTableView
        logs={logs}
        columns={columns}
        isLoading={isLoading}
        page={page}
        setPage={setPage}
        pageSize={pageSize}
        setPageSize={setPageSize}
        total={total}
        onRefresh={refetch}
      />

      <LogDetailSheet
        selectedLog={selectedLog}
        isDetailOpen={isDetailOpen}
        setIsDetailOpen={setIsDetailOpen}
        formatJson={formatJson}
      />
    </div>
  );
}
