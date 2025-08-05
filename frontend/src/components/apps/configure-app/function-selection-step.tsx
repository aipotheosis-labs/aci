import { EnhancedDataTable } from "@/components/ui-extensions/enhanced-data-table/data-table";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { DialogFooter } from "@/components/ui/dialog";
import { RowSelectionState } from "@tanstack/react-table";
import * as z from "zod";
import { useUpdateAppConfig } from "@/hooks/use-app-config";
import { useApp } from "@/hooks/use-app";
import { toast } from "sonner";
import { useEffect, useState } from "react";
import { useAppFunctionsColumns } from "../useAppFunctionsColumns";
import { AppFunction } from "@/lib/types/appfunction";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";

// Form schema for agent selection
export const agentSelectFormSchema = z.object({
  agents: z.array(z.string()).optional(),
});

export type AgentSelectFormValues = z.infer<typeof agentSelectFormSchema>;

interface FunctionSelectionStepProps {
  onNext: () => void;
  appName: string;
  isDialogOpen: boolean;
}

export function FunctionSelectionStep({
  onNext,
  appName,
  isDialogOpen,
}: FunctionSelectionStepProps) {
  const [selectedFunctionNames, setSelectedFunctionNames] =
    useState<RowSelectionState>({});
  const [functions, setFunctions] = useState<AppFunction[]>([]);
  const [isAllFunctionsEnabled, setIsAllFunctionsEnabled] = useState(false);

  const { app } = useApp(appName);
  const {
    mutateAsync: updateAppConfigMutation,
    isPending: isUpdatingAppConfig,
  } = useUpdateAppConfig();

  // Load available functions from the app
  useEffect(() => {
    if (app) {
      setFunctions(app.functions);
    }
    setIsAllFunctionsEnabled(true);
  }, [app]);

  // By default select all available functions
  useEffect(() => {
    if (isDialogOpen && app?.functions) {
      const initialSelection: RowSelectionState = {};
      app.functions.forEach((func: AppFunction) => {
        if (func.name) {
          initialSelection[func.name] = true;
        }
      });
      setSelectedFunctionNames(initialSelection);
    }
  }, [isDialogOpen, app]);

  // construct the functions table
  const columns = useAppFunctionsColumns();

  // Handle when user click confirm button
  const handleNext = async () => {
    if (Object.keys(selectedFunctionNames).length === 0) {
      onNext();
      return;
    }

    try {
      if (isAllFunctionsEnabled) {
        await updateAppConfigMutation({
          app_name: appName,
          enabled: true,
          all_functions_enabled: true,
          enabled_functions: [],
        });
      } else {
        const enabledFunctions = functions.filter(
          (func) => selectedFunctionNames[func.name],
        );
        const enabledFunctionsNames = enabledFunctions.map((func) => func.name);

        await updateAppConfigMutation({
          app_name: appName,
          enabled: true,
          all_functions_enabled: false,
          enabled_functions: enabledFunctionsNames,
        });
      }

      toast.success("Updated enabled functions successfully");
      onNext();
    } catch (error) {
      console.error("Failed to update enabled functions:", error);
      toast.error("Failed to update enabled functions. Please try again.");
    }
  };

  return (
    <div className="space-y-2">
      {functions.length > 0 ? (
        <div>
          <div className="flex items-center gap-2">
            <Switch
              checked={isAllFunctionsEnabled}
              onCheckedChange={setIsAllFunctionsEnabled}
            />
            <Label className="text-sm font-medium">
              Enable All Available Functions
            </Label>
          </div>

          {!isAllFunctionsEnabled && (
            <div className="mt-4">
              <div className="flex items-center gap-2">
                <h3 className="text-sm font-medium">Selected Functions</h3>
                <Badge
                  variant="secondary"
                  className="flex items-center gap-1 px-2 py-1 text-xs"
                >
                  Selected {Object.keys(selectedFunctionNames).length} Functions
                </Badge>
              </div>
              <EnhancedDataTable
                columns={columns}
                data={functions}
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

      <DialogFooter>
        <Button
          type="button"
          onClick={handleNext}
          disabled={isUpdatingAppConfig}
        >
          {isUpdatingAppConfig ? "Confirming..." : "Confirm"}
        </Button>
      </DialogFooter>
    </div>
  );
}
