"use client";

import { useState, useMemo } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Eye } from "lucide-react";
import { createColumnHelper, type ColumnDef } from "@tanstack/react-table";
import { EnhancedDataTable } from "@/components/ui-extensions/enhanced-data-table/data-table";
import { ArrowUpDown } from "lucide-react";

// Configuration
export const LOGS_CONFIG = {
  refreshInterval: 30000, // 30 seconds
  maxLogsPerPage: 50,
  logTypes: {
    API: "api",
    SYSTEM: "system",
    ALL: "all",
  },
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

export type LogType =
  (typeof LOGS_CONFIG.logTypes)[keyof typeof LOGS_CONFIG.logTypes];
export type LogStatus = keyof typeof LOGS_CONFIG.statusColors;

// Types
interface LogEntry {
  id: string;
  timestamp: string;
  appName: string;
  functionName: string;
  input: string;
  output: string;
  status: LogStatus;
  type: "api" | "system";
}

const columnHelper = createColumnHelper<LogEntry>();

// Custom hook for table data and operations
const useLogsTable = () => {
  const [selectedLog, setSelectedLog] = useState<LogEntry | null>(null);
  const [isDetailOpen, setIsDetailOpen] = useState(false);

  // Mock data - replace with actual data fetching
  const logs: LogEntry[] = [
    {
      id: "1",
      timestamp: "2024-03-20T10:00:00Z",
      appName: "app1",
      functionName: "function1",
      input: '{"key": "value"}',
      output: '{"result": "success"}',
      status: "success",
      type: "api",
    },
    {
      id: "2",
      timestamp: "2024-03-20T10:01:00Z",
      appName: "app2",
      functionName: "function2",
      input: '{"check": "system"}',
      output: '{"status": "healthy"}',
      status: "info",
      type: "system",
    },
  ];

  const getJsonPreview = (jsonStr: string) => {
    try {
      const obj = JSON.parse(jsonStr);
      const firstKey = Object.keys(obj)[0];
      const firstValue = obj[firstKey];
      return `${firstKey}: ${typeof firstValue === "string" ? firstValue : JSON.stringify(firstValue)}`;
    } catch {
      return jsonStr;
    }
  };

  const formatJson = (jsonStr: string) => {
    try {
      const obj = JSON.parse(jsonStr);
      return JSON.stringify(obj, null, 2);
    } catch {
      return jsonStr;
    }
  };

  return {
    logs,
    selectedLog,
    setSelectedLog,
    isDetailOpen,
    setIsDetailOpen,
    getJsonPreview,
    formatJson,
  };
};

// Table columns definition
const useTableColumns = (
  setSelectedLog: (log: LogEntry) => void,
  setIsDetailOpen: (isOpen: boolean) => void,
  getJsonPreview: (jsonStr: string) => string,
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
        cell: (info) => new Date(info.getValue()).toLocaleString(),
        enableGlobalFilter: true,
      }),
      columnHelper.accessor("appName", {
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
        cell: (info) => info.getValue(),
        enableGlobalFilter: true,
      }),
      columnHelper.accessor("functionName", {
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
        cell: (info) => info.getValue(),
        enableGlobalFilter: true,
      }),
      columnHelper.accessor("input", {
        header: "INPUT",
        cell: (info) => getJsonPreview(info.getValue()),
        enableGlobalFilter: true,
      }),
      columnHelper.accessor("output", {
        header: "OUTPUT",
        cell: (info) => getJsonPreview(info.getValue()),
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
}: {
  logs: LogEntry[];
  columns: ColumnDef<LogEntry>[];
}) => {
  if (logs.length === 0) {
    return (
      <div className="text-center p-8 text-muted-foreground">No logs found</div>
    );
  }

  return (
    <EnhancedDataTable
      columns={columns}
      data={logs}
      defaultSorting={[{ id: "timestamp", desc: true }]}
      searchBarProps={{
        placeholder: "Search logs",
      }}
      paginationOptions={{
        initialPageIndex: 0,
        initialPageSize: 15,
      }}
    />
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
  formatJson: (jsonStr: string) => string;
}) => {
  if (!selectedLog) return null;

  return (
    <Sheet open={isDetailOpen} onOpenChange={setIsDetailOpen}>
      <SheetContent className="w-[600px] sm:w-[800px]">
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
                  <p>{new Date(selectedLog.timestamp).toLocaleString()}</p>
                </div>
                <div>
                  <span className="text-muted-foreground">App Name:</span>
                  <p>{selectedLog.appName}</p>
                </div>
                <div>
                  <span className="text-muted-foreground">Function:</span>
                  <p>{selectedLog.functionName}</p>
                </div>
                <div>
                  <span className="text-muted-foreground">Status:</span>
                  <p
                    className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${LOGS_CONFIG.statusColors[selectedLog.status].bg} ${LOGS_CONFIG.statusColors[selectedLog.status].text}`}
                  >
                    {selectedLog.status}
                  </p>
                </div>
              </div>
            </div>

            <div>
              <h3 className="text-sm font-medium mb-2">Input</h3>
              <pre className="bg-muted p-4 rounded-lg overflow-auto text-sm">
                {formatJson(selectedLog.input)}
              </pre>
            </div>

            <div>
              <h3 className="text-sm font-medium mb-2">Output</h3>
              <pre className="bg-muted p-4 rounded-lg overflow-auto text-sm">
                {formatJson(selectedLog.output)}
              </pre>
            </div>
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
    selectedLog,
    setSelectedLog,
    isDetailOpen,
    setIsDetailOpen,
    getJsonPreview,
    formatJson,
  } = useLogsTable();

  const columns = useTableColumns(
    setSelectedLog,
    setIsDetailOpen,
    getJsonPreview,
  );

  return (
    <div className="container mx-auto py-6 space-y-6 h-full">
      <Card className="border-none h-full">
        <CardContent className="h-full">
          <LogsTableView logs={logs} columns={columns} />
        </CardContent>
      </Card>

      <LogDetailSheet
        selectedLog={selectedLog}
        isDetailOpen={isDetailOpen}
        setIsDetailOpen={setIsDetailOpen}
        formatJson={formatJson}
      />
    </div>
  );
}
