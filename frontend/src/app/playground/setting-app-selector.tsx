"use client";

import { useState } from "react";
import { Wrench, Check, ChevronsUpDown } from "lucide-react";
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
import Image from "next/image";
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
// Maximum number of apps that can be selected
const MAX_APPS = Number(process.env.NEXT_PUBLIC_AGENT_MAX_APPS) || 10;

export function AppMultiSelector() {
  const [open, setOpen] = useState(false);

  const {
    selectedApps,
    setSelectedApps,
    getAvailableApps,
    selectedFunctions,
    setSelectedFunctions,
    appFunctions,
  } = useAgentStore(
    useShallow((state) => ({
      selectedApps: state.selectedApps,
      setSelectedApps: state.setSelectedApps,
      getAvailableApps: state.getAvailableApps,
      selectedFunctions: state.selectedFunctions,
      setSelectedFunctions: state.setSelectedFunctions,
      appFunctions: state.appFunctions,
    })),
  );

  const availableApps = getAvailableApps();
  const availableAppIds = availableApps.map((app) => app.name);
  const allSelected =
    availableAppIds.length > 0 &&
    availableAppIds.length === selectedApps.length;

  const appList = availableApps.map((app) => ({
    id: app.name,
    name: app.display_name || app.name,
    icon: (
      <div className="size-4 relative">
        <Image
          src={app.logo || ""}
          alt={`${app.display_name || app.name} icon`}
          width={16}
          height={16}
          className="object-contain"
        />
      </div>
    ),
  }));

  const handleAppChange = (appId: string) => {
    if (selectedApps.includes(appId)) {
      setSelectedApps(selectedApps.filter((id) => id !== appId));
      // also remove all functions related to the app
      const functionsForApp = appFunctions
        .filter((func) => func.name.startsWith(`${appId.toUpperCase()}__`))
        .map((func) => func.name);
      setSelectedFunctions(
        selectedFunctions.filter(
          (funcName) => !functionsForApp.includes(funcName),
        ),
      );
    } else {
      if (selectedApps.length >= MAX_APPS) {
        toast.error(`You can only select up to ${MAX_APPS} apps at a time`);
        return;
      }
      setSelectedApps([...selectedApps, appId]);
    }
  };

  const handleSelectAll = () => {
    if (allSelected) {
      setSelectedApps([]);
      setSelectedFunctions([]);
    } else {
      if (availableAppIds.length > MAX_APPS) {
        toast.error(
          `You can only select up to ${MAX_APPS} apps. Cannot select all ${availableAppIds.length} apps.`,
        );
        return;
      }
      setSelectedApps(availableAppIds);
    }
  };

  return (
    <div className="space-y-2">
      <Tooltip>
        <div className="flex items-center gap-2">
          <h3 className="text-sm font-medium">Apps</h3>
          <TooltipTrigger asChild>
            <BsQuestionCircle className="h-4 w-4 text-muted-foreground" />
          </TooltipTrigger>
        </div>
        <TooltipContent>
          <p>
            Select from the agent&apos;s enabled apps, check manage project
            panel.
          </p>
        </TooltipContent>
      </Tooltip>
      <Popover open={open} onOpenChange={setOpen} key="app-selector-popover">
        <PopoverTrigger asChild>
          <Button
            variant="outline"
            size="sm"
            className="w-full rounded-md h-8 bg-transparent border-input flex justify-start items-center hover:bg-accent hover:text-accent-foreground transition-colors px-3 h-9"
            aria-label={`Apps: ${selectedApps.length === 0 ? "All" : `${selectedApps.length} selected`}`}
          >
            <div className="flex items-center gap-3">
              <Wrench className="size-4 text-muted-foreground" />
              <span className="text-sm font-medium">Apps</span>
            </div>
            <div className="ml-auto">
              {selectedApps.length > 0 ? (
                <Badge className="size-4 px-1.5 flex items-center justify-center text-xs font-medium bg-primary text-primary-foreground">
                  {selectedApps.length}
                </Badge>
              ) : (
                <Badge
                  variant="outline"
                  className="py-0.5 px-2 flex items-center justify-center text-xs font-medium"
                >
                  None
                </Badge>
              )}
            </div>
            <ChevronsUpDown className="h-4 w-4 shrink-0 opacity-50" />
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-[var(--radix-popover-trigger-width)] p-0">
          <Command className="rounded-lg shadow-md">
            <CommandInput placeholder="Search apps..." />
            <CommandList>
              <CommandEmpty>No apps found.</CommandEmpty>
              <CommandGroup>
                {availableAppIds.length > 0 && (
                  <CommandItem
                    key="select-all"
                    onSelect={handleSelectAll}
                    className="flex items-center justify-between"
                  >
                    <div className="flex items-center gap-2 flex-1">
                      <span>{allSelected ? "Deselect All" : "Select All"}</span>
                    </div>
                    <Check
                      className={cn(
                        "h-4 w-4",
                        allSelected ? "opacity-100" : "opacity-0",
                      )}
                    />
                  </CommandItem>
                )}
                <div className="h-px bg-border my-1" />
                {appList.map((app) => (
                  <CommandItem
                    key={app.id}
                    value={app.id}
                    onSelect={() => handleAppChange(app.id)}
                    className="flex items-center justify-between"
                  >
                    <div className="flex items-center gap-2 flex-1">
                      {app.icon}
                      <span>{app.name}</span>
                    </div>
                    <Check
                      className={cn(
                        "h-4 w-4",
                        selectedApps.includes(app.id)
                          ? "opacity-100"
                          : "opacity-0",
                      )}
                    />
                  </CommandItem>
                ))}
              </CommandGroup>
            </CommandList>
          </Command>
        </PopoverContent>
      </Popover>
    </div>
  );
}
