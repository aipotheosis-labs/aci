"use client";

import { useState } from "react";
import { Code, Check, Loader2, ChevronsUpDown } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command";
import { Badge } from "@/components/ui/badge";
import { useAgentStore } from "@/lib/store/agent";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import {
  Tooltip,
  TooltipTrigger,
  TooltipContent,
} from "@/components/ui/tooltip";
import { BsQuestionCircle } from "react-icons/bs";
import { useShallow } from "zustand/react/shallow";
export function FunctionMultiSelector() {
  const [open, setOpen] = useState(false);

  const {
    selectedFunctions,
    setSelectedFunctions,
    getAvailableAppFunctions,
    loadingFunctions,
  } = useAgentStore(
    useShallow((state) => ({
      selectedFunctions: state.selectedFunctions,
      setSelectedFunctions: state.setSelectedFunctions,
      getAvailableAppFunctions: state.getAvailableAppFunctions,
      loadingFunctions: state.loadingFunctions,
    })),
  );
  const appFunctions = getAvailableAppFunctions();

  const handleFunctionChange = (functionName: string) => {
    if (selectedFunctions.includes(functionName)) {
      setSelectedFunctions(
        selectedFunctions.filter((name) => name !== functionName),
      );
    } else {
      setSelectedFunctions([...selectedFunctions, functionName]);
    }
  };

  return (
    <div className="space-y-2">
      <Tooltip>
        <div className="flex items-center gap-2">
          <h3 className="text-sm font-medium">Functions</h3>
          <TooltipTrigger asChild>
            <BsQuestionCircle className="h-4 w-4 text-muted-foreground" />
          </TooltipTrigger>
        </div>
        <TooltipContent>
          <p>Select functions from selected apps.</p>
        </TooltipContent>
      </Tooltip>
      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger asChild>
          <Button
            variant="outline"
            size="sm"
            className="w-full rounded-md h-8 bg-transparent border-input flex justify-start items-center hover:bg-accent hover:text-accent-foreground transition-colors px-3 h-9"
            aria-label={`Functions: ${selectedFunctions.length === 0 ? "All" : `${selectedFunctions.length} selected`}`}
          >
            <div className="flex items-center gap-3">
              <Code className="size-4 text-muted-foreground" />
              <span className="text-sm font-medium">Functions</span>
            </div>
            <div className="ml-auto">
              {loadingFunctions ? (
                <Loader2 className="size-4 animate-spin" />
              ) : (
                <>
                  {selectedFunctions.length > 0 ? (
                    <Badge className="size-4 px-1.5 flex items-center justify-center text-xs font-medium bg-primary text-primary-foreground">
                      {selectedFunctions.length}
                    </Badge>
                  ) : (
                    <Badge
                      variant="outline"
                      className="py-0.5 px-2 flex items-center justify-center text-xs font-medium"
                    >
                      None
                    </Badge>
                  )}
                </>
              )}
            </div>
            <ChevronsUpDown className="h-4 w-4 shrink-0 opacity-50" />
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-[var(--radix-popover-trigger-width)] p-0">
          <Command className="rounded-lg shadow-md">
            <CommandInput placeholder="Search functions..." />
            <CommandList>
              <CommandEmpty>No functions found.</CommandEmpty>
              <CommandGroup>
                {loadingFunctions ? (
                  <div className="text-sm text-muted-foreground p-2">
                    Loading functions...
                  </div>
                ) : (
                  <>
                    <div className="h-px bg-border my-1" />
                    {appFunctions.map((func) => (
                      <CommandItem
                        key={`function-${func.name}`}
                        value={func.name}
                        onSelect={() => handleFunctionChange(func.name)}
                        className="flex items-center justify-between"
                        data-value={func.name}
                      >
                        <Check
                          className={cn(
                            "h-4 w-4",
                            selectedFunctions.includes(func.name)
                              ? "opacity-100"
                              : "opacity-0",
                          )}
                        />
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <div
                              className={cn(
                                "flex flex-col gap-1 flex-1 px-2 py-1 rounded-md",
                                selectedFunctions.includes(func.name)
                                  ? "bg-slate-300 text-accent-foreground"
                                  : "hover:bg-muted",
                              )}
                            >
                              <span className="text-sm">{func.name}</span>
                            </div>
                          </TooltipTrigger>
                          <TooltipContent>
                            <p>{func.name}</p>
                          </TooltipContent>
                        </Tooltip>
                      </CommandItem>
                    ))}
                  </>
                )}
              </CommandGroup>
            </CommandList>
          </Command>
        </PopoverContent>
      </Popover>
    </div>
  );
}
