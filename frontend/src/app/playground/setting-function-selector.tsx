"use client";

import { useEffect, useState } from "react";
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
import { toast } from "sonner";
import { useMetaInfo } from "@/components/context/metainfo";
import { getApiKey } from "@/lib/api/util";
import { useAgentStore } from "@/lib/store/agent";
import { searchFunctions } from "@/lib/api/appfunction";
import { AppFunction } from "@/lib/types/appfunction";
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
export function FunctionMultiSelector() {
  const [open, setOpen] = useState(false);
  const [functions, setFunctions] = useState<AppFunction[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const { activeProject } = useMetaInfo();
  const { selectedFunctions, setSelectedFunctions, selectedApps } =
    useAgentStore();

  useEffect(() => {
    const fetchFunctions = async () => {
      if (selectedApps.length === 0) {
        setSelectedFunctions([]);
        return;
      }
      if (!activeProject) {
        console.warn("No active project");
        setIsLoading(false);
        return;
      }

      try {
        const apiKey = getApiKey(activeProject);
        let functionsData = await searchFunctions(
          {
            allowed_apps_only: true,
          },
          apiKey,
        );
        functionsData = functionsData
          .filter((func) =>
            selectedApps.some((appName) =>
              func.name.startsWith(`${appName.toUpperCase()}__`),
            ),
          )
          .sort((a, b) => a.name.localeCompare(b.name));
        setFunctions(functionsData);
      } catch (error) {
        console.error("Failed to fetch functions:", error);
        toast.error("Failed to load functions");
      } finally {
        setIsLoading(false);
      }
    };
    console.log("selectedApps has changed", selectedApps);

    fetchFunctions();
  }, [activeProject, selectedApps, setSelectedFunctions]);

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
              {isLoading ? (
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
                {isLoading ? (
                  <div className="text-sm text-muted-foreground p-2">
                    Loading functions...
                  </div>
                ) : (
                  <>
                    <div className="h-px bg-border my-1" />
                    {functions.map((func) => (
                      <CommandItem
                        key={`function-${func.name}`}
                        value={func.name}
                        onSelect={() => handleFunctionChange(func.name)}
                        className="flex items-center justify-between"
                        data-value={func.name}
                      >
                        <div className="flex flex-col gap-1 flex-1">
                          <span>{func.name}</span>
                        </div>
                        <Check
                          className={cn(
                            "h-4 w-4",
                            selectedFunctions.includes(func.name)
                              ? "opacity-100"
                              : "opacity-0",
                          )}
                        />
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
