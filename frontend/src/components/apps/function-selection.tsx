import { EnhancedDataTable } from "@/components/ui-extensions/enhanced-data-table/data-table";
import { Badge } from "@/components/ui/badge";
import { RowSelectionState } from "@tanstack/react-table";
import { Dispatch, SetStateAction } from "react";
import { useAppFunctionsColumns } from "./useAppFunctionsColumns";
import { AppFunction } from "@/lib/types/appfunction";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { BsInfoCircle } from "react-icons/bs";

interface FunctionSelectionProps {
  availableFunctions: AppFunction[];
  isAllFunctionsEnabled: boolean;
  setIsAllFunctionsEnabled: (isAllFunctionsEnabled: boolean) => void;
  selectedFunctionNames: RowSelectionState;
  setSelectedFunctionNames: Dispatch<SetStateAction<RowSelectionState>>;
}

export function FunctionSelection({
  availableFunctions,
  isAllFunctionsEnabled,
  setIsAllFunctionsEnabled,
  selectedFunctionNames,
  setSelectedFunctionNames,
}: FunctionSelectionProps) {
  const columns = useAppFunctionsColumns();

  return (
    <div className="space-y-2">
      {availableFunctions.length > 0 ? (
        <div>
          <div className="flex items-center gap-2">
            <Switch
              checked={isAllFunctionsEnabled}
              onCheckedChange={setIsAllFunctionsEnabled}
            />
            <Label className="text-sm font-medium">
              Enable All Available Functions
            </Label>
            <Tooltip>
              <TooltipTrigger asChild>
                <span className="cursor-pointer">
                  <BsInfoCircle className="h-4 w-4 text-muted-foreground" />
                </span>
              </TooltipTrigger>
              <TooltipContent side="top">
                <p className="text-xs">
                  New functions available in the future for the app will be
                  enabled automatically.
                </p>
              </TooltipContent>
            </Tooltip>
          </div>

          {!isAllFunctionsEnabled && (
            <div className="mt-4">
              <div className="flex items-center gap-2">
                <h3 className="text-sm font-medium">Enabled Functions</h3>
                <Badge
                  variant="secondary"
                  className="flex items-center gap-1 px-2 py-1 text-xs"
                >
                  Selected {Object.keys(selectedFunctionNames).length} Functions
                </Badge>
              </div>
              <EnhancedDataTable
                columns={columns}
                data={availableFunctions}
                searchBarProps={{ placeholder: "Search functions..." }}
                rowSelectionProps={{
                  rowSelection: selectedFunctionNames,
                  onRowSelectionChange: setSelectedFunctionNames,
                  getRowId: (row) => row.name,
                }}
                paginationOptions={{
                  initialPageIndex: 0,
                  initialPageSize: 15,
                }}
              />
            </div>
          )}
        </div>
      ) : (
        <div className="flex items-center justify-center p-8 border rounded-md">
          <p className="text-muted-foreground">No Available Functions</p>
        </div>
      )}
    </div>
  );
}
