"use client";

import { Check, ChevronsUpDown, Building } from "lucide-react";

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
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { useState } from "react";
import { Skeleton } from "@/components/ui/skeleton";
import { useMetaInfo } from "@/components/context/metainfo";

export const OrgSelector = () => {
  const { orgs, activeOrg, setActiveOrg } = useMetaInfo();
  const [open, setOpen] = useState(false);

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="ghost"
          role="combobox"
          aria-expanded={open}
          className="w-full justify-between h-9 px-2 text-sm font-medium hover:bg-gray-50 border border-gray-200 rounded-md"
        >
          <div className="flex items-center gap-2 truncate">
            <Building className="h-3 w-3 text-gray-500 flex-shrink-0" />
            {activeOrg ? (
              <span className="truncate">{activeOrg.orgName}</span>
            ) : (
              <Skeleton className="h-3 w-20" />
            )}
          </div>
          <ChevronsUpDown className="h-3 w-3 opacity-50 flex-shrink-0" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-64 p-0" align="start">
        <Command>
          <CommandInput placeholder="Search organization..." className="h-9" />
          <CommandList>
            <CommandEmpty>No organization found.</CommandEmpty>
            <CommandGroup>
              {orgs.map((org) => (
                <CommandItem
                  key={org.orgId}
                  value={org.orgId}
                  onSelect={() => {
                    setActiveOrg(org);
                    setOpen(false);
                  }}
                  className="flex justify-between items-center relative"
                >
                  <div className="flex items-center gap-2 w-full">
                    <Building className="h-4 w-4 text-gray-400" />
                    <div className="flex-grow truncate">{org.orgName}</div>
                    <Check
                      className={cn(
                        "h-4 w-4",
                        activeOrg?.orgId === org.orgId
                          ? "opacity-100"
                          : "opacity-0",
                      )}
                    />
                  </div>
                </CommandItem>
              ))}
            </CommandGroup>
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  );
};
