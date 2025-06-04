"use client";

import { Check, ChevronsUpDown } from "lucide-react";

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
          variant="outline"
          role="combobox"
          aria-expanded={open}
          className="w-full justify-between"
        >
          {activeOrg ? activeOrg.orgName : <Skeleton className="h-4 w-24" />}
          <ChevronsUpDown className="opacity-50" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-full p-0">
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
                  <div className="flex justify-between items-center w-full">
                    <div className="flex-grow">{org.orgName}</div>
                    <div className="flex items-center">
                      <Check
                        className={cn(
                          "mr-2",
                          activeOrg?.orgId === org.orgId
                            ? "opacity-100"
                            : "opacity-0",
                        )}
                      />
                    </div>
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
