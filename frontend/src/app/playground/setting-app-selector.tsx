"use client";

import { useEffect, useState, useRef } from "react";
import { Wrench, Check, Loader2, ChevronsUpDown } from "lucide-react";
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
import { useMetaInfo } from "@/components/context/metainfo";
import { getApiKey } from "@/lib/api/util";
import { getApps } from "@/lib/api/app";
import { App } from "@/lib/types/app";
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
// Maximum number of apps that can be selected
const MAX_APPS = 6;

export function AppMultiSelector() {
  const [open, setOpen] = useState(false);
  const [apps, setApps] = useState<App[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const { activeProject } = useMetaInfo();
  const {
    selectedApps,
    setSelectedApps,
    allowedApps,
    linkedAccountOwnerId,
    selectedAgent,
  } = useAgentStore();
  const previousLinkedAccountOwnerIdRef = useRef<string | null>(null);
  const previousSelectedAgentRef = useRef<string | null>(null);

  useEffect(() => {
    const fetchApps = async () => {
      if (!activeProject) {
        console.warn("No active project");
        setIsLoading(false);
        return;
      }

      try {
        const apiKey = getApiKey(activeProject);
        const appsData = await getApps([], apiKey);
        const filteredApps = appsData.filter((app) =>
          allowedApps.includes(app.name),
        );
        setApps(filteredApps);
      } catch (error) {
        console.error("Failed to fetch apps:", error);
        toast.error("Failed to load apps");
      } finally {
        setIsLoading(false);
      }
    };

    fetchApps();
  }, [activeProject, allowedApps]);

  useEffect(() => {
    console.log("linkedAccountOwnerId", linkedAccountOwnerId);
    if (!linkedAccountOwnerId) {
      setSelectedApps([]);
    }
    if (linkedAccountOwnerId !== previousLinkedAccountOwnerIdRef.current) {
      setSelectedApps([]);
    }
    if (selectedAgent !== previousSelectedAgentRef.current) {
      setSelectedApps([]);
    }
    previousLinkedAccountOwnerIdRef.current = linkedAccountOwnerId;
    previousSelectedAgentRef.current = selectedAgent;
  }, [linkedAccountOwnerId, selectedAgent, setSelectedApps]);

  const appList = apps.map((app) => ({
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
    } else {
      if (selectedApps.length >= MAX_APPS) {
        toast.error(`You can only select up to ${MAX_APPS} apps at a time`);
        return;
      }
      setSelectedApps([...selectedApps, appId]);
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
              {isLoading ? (
                <Loader2 className="size-4 animate-spin" />
              ) : (
                <>
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
                </>
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
                {isLoading ? (
                  <div className="text-sm text-muted-foreground p-2">
                    Loading apps...
                  </div>
                ) : (
                  <>
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
