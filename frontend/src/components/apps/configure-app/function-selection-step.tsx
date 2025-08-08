import { Button } from "@/components/ui/button";
import { DialogFooter } from "@/components/ui/dialog";
import { RowSelectionState } from "@tanstack/react-table";
import { useUpdateAppConfig } from "@/hooks/use-app-config";
import { useApp } from "@/hooks/use-app";
import { toast } from "sonner";
import { useEffect, useState } from "react";
import { AppFunction } from "@/lib/types/appfunction";
import { FunctionSelection } from "../function-selection";

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
      <FunctionSelection
        availableFunctions={functions}
        isAllFunctionsEnabled={isAllFunctionsEnabled}
        setIsAllFunctionsEnabled={setIsAllFunctionsEnabled}
        selectedFunctionNames={selectedFunctionNames}
        setSelectedFunctionNames={setSelectedFunctionNames}
      />

      <DialogFooter className="mt-4">
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
