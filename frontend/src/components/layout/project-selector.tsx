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
  CommandSeparator,
} from "@/components/ui/command";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { useEffect, useState } from "react";
import { Skeleton } from "@/components/ui/skeleton";
import { useMetaInfo } from "@/components/context/metainfo";
import { GoPlus } from "react-icons/go";

interface ProjectSelectOption {
  value: string; // project id
  label: string; // project name
}

export const ProjectSelector = () => {
  const { projects, activeProject, setActiveProject } = useMetaInfo();
  const [projectSelectOptions, setProjectSelectOptions] = useState<
    ProjectSelectOption[]
  >([]);

  const [open, setOpen] = useState(false);

  useEffect(() => {
    setProjectSelectOptions(
      projects.map((p) => ({
        value: p.id,
        label: p.name,
      })),
    );
  }, [projects]);

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
              {projectSelectOptions.map((option) => (
                <CommandItem
                  key={option.value}
                  value={option.value}
                  onSelect={() => {
                    const selectedProject = projects.find(
                      (p) => p.id === option.value,
                    );
                    if (selectedProject) {
                      setActiveProject(selectedProject);
                      setOpen(false);
                    } else {
                      console.error(`Project ${option.value} not found`);
                    }
                  }}
                >
                  {option.label}
                  <Check
                    className={cn(
                      "ml-auto",
                      activeProject?.id === option.value
                        ? "opacity-100"
                        : "opacity-0",
                    )}
                  />
                </CommandItem>
              ))}
            </CommandGroup>
            <CommandSeparator />
            <CommandGroup>
              <CommandItem>
                <GoPlus />
                <span>Create Project</span>
              </CommandItem>
            </CommandGroup>
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  );
};
