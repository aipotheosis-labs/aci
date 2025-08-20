"use client";

import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { BsQuestionCircle } from "react-icons/bs";
import {
  Tooltip,
  TooltipTrigger,
  TooltipContent,
} from "@/components/ui/tooltip";
import { useCallback, useEffect, useState } from "react";
import { FunctionSelection } from "../apps/function-selection";
import { RowSelectionState } from "@tanstack/react-table";
import { useApp } from "@/hooks/use-app";
import { useAppConfig, useUpdateAppConfig } from "@/hooks/use-app-config";
import { AppFunction } from "@/lib/types/appfunction";
import { GoMultiSelect } from "react-icons/go";
import { toast } from "sonner";

interface FunctionSelectionDialogProps {
  appName: string;
  onSave: () => void;
}

export function FunctionSelectionDialog({
  appName,
}: FunctionSelectionDialogProps) {
  const [open, setOpen] = useState(false);

  const [selectedFunctionNames, setSelectedFunctionNames] =
    useState<RowSelectionState>({});
  const [functions, setFunctions] = useState<AppFunction[]>([]);
  const [isAllFunctionsEnabled, setIsAllFunctionsEnabled] = useState(false);

  const { app } = useApp(appName);

  const { data: appConfig } = useAppConfig(appName);
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
    if (app?.functions) {
      const initialSelection: RowSelectionState = {};
      app.functions.forEach((func: AppFunction) => {
        if (func.name) {
          initialSelection[func.name] = true;
        }
      });
      setSelectedFunctionNames(initialSelection);
    }
  }, [app]);

  const populateSelectedFunctionNames = () => {
    const initialSelection: RowSelectionState = {};
    if (appConfig?.all_functions_enabled) {
      setIsAllFunctionsEnabled(true);
    } else if (appConfig?.enabled_functions) {
      setIsAllFunctionsEnabled(false);
      appConfig.enabled_functions.forEach((func: string) => {
        if (func) {
          initialSelection[func] = true;
        }
      });
    }
    setSelectedFunctionNames(initialSelection);
  };

  const handleSave = useCallback(async () => {
    try {
      if (isAllFunctionsEnabled) {
        await updateAppConfigMutation({
          app_name: appName,
          all_functions_enabled: true,
          enabled_functions: [],
        });
      } else {
        const enabledFunctions = app?.functions.filter(
          (func: AppFunction) => selectedFunctionNames[func.name],
        );
        const enabledFunctionsNames = enabledFunctions?.map(
          (func: AppFunction) => func.name,
        );
        await updateAppConfigMutation({
          app_name: appName,
          all_functions_enabled: false,
          enabled_functions: enabledFunctionsNames,
        });
      }
      setOpen(false);
      toast.success("Functions updated successfully");
    } catch (error) {
      console.error("Failed to update app config:", error);
    }
  }, [
    appName,
    isAllFunctionsEnabled,
    selectedFunctionNames,
    app,
    updateAppConfigMutation,
  ]);

  return (
    <Dialog
      open={open}
      onOpenChange={(open) => {
        setOpen(open);
        if (open) {
          populateSelectedFunctionNames();
        }
      }}
    >
      <div className="flex items-center gap-2">
        <DialogTrigger asChild>
          <Button>
            <GoMultiSelect />
            Select Functions
            <Tooltip>
              <TooltipTrigger asChild>
                <span className="cursor-pointer">
                  <BsQuestionCircle className="h-4 w-4 " />
                </span>
              </TooltipTrigger>
              <TooltipContent side="top">
                <p className="text-xs">{"Enable/Disable functions"}</p>
              </TooltipContent>
            </Tooltip>
          </Button>
        </DialogTrigger>
      </div>

      <DialogContent className="sm:max-w-[65vw]">
        <DialogHeader>
          <DialogTitle>Enable/Disable functions</DialogTitle>
        </DialogHeader>
        <div className="mt-2 overflow-y-auto max-h-[70vh]">
          <FunctionSelection
            availableFunctions={functions}
            isAllFunctionsEnabled={isAllFunctionsEnabled}
            setIsAllFunctionsEnabled={setIsAllFunctionsEnabled}
            selectedFunctionNames={selectedFunctionNames}
            setSelectedFunctionNames={setSelectedFunctionNames}
          />
        </div>
        <div className="flex justify-end gap-2 mt-4">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setOpen(false)}
            disabled={isUpdatingAppConfig}
            // className="me-1"
          >
            Cancel
          </Button>

          <Button
            variant="default"
            size="sm"
            onClick={() => handleSave()}
            disabled={isUpdatingAppConfig}
          >
            {isUpdatingAppConfig ? "Saving..." : "Save"}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
