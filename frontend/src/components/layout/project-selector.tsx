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
// import { GoPlus } from "react-icons/go";
import { useMetaInfo } from "@/components/context/metainfo";

export const ProjectSelector = () => {
  const { projects, activeProject, setActiveProject } = useMetaInfo();

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
          {activeProject ? (
            activeProject.name
          ) : (
            <Skeleton className="h-4 w-24" />
          )}
          <ChevronsUpDown className="opacity-50" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-full p-0">
        <Command>
          <CommandInput placeholder="Search project..." className="h-9" />
          <CommandList>
            <CommandEmpty>No project found.</CommandEmpty>
            <CommandGroup>
              {projects.map((project) => (
                <CommandItem
                  key={project.id}
                  value={project.id}
                  onSelect={() => {
                    setActiveProject(project);
                    setOpen(false);
                  }}
                >
                  {project.name}
                  <Check
                    className={cn(
                      "ml-auto",
                      activeProject?.id === project.id
                        ? "opacity-100"
                        : "opacity-0",
                    )}
                  />
                </CommandItem>
              ))}
            </CommandGroup>
            {/* <CommandSeparator />
            <CommandGroup>
              <CommandItem>
                <GoPlus />
                <span>Create Project</span>
              </CommandItem>
            </CommandGroup> */}
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  );
};
