"use client";

import { Check, ChevronsUpDown, FolderOpen } from "lucide-react";

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
import { useState } from "react";
import { Skeleton } from "@/components/ui/skeleton";
import { useMetaInfo } from "@/components/context/metainfo";
import { GoPlus } from "react-icons/go";
import { CreateProjectDialog } from "@/components/project/create-project-dialog";

export const ProjectSelector = () => {
  const { projects, activeProject, setActiveProject, reloadActiveProject } =
    useMetaInfo();
  const [open, setOpen] = useState(false);
  const [openCreateDialog, setOpenCreateDialog] = useState(false);

  const handleCreateProjectClick = () => {
    setOpen(false);
    setOpenCreateDialog(true);
  };

  return (
    <>
      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger asChild>
          <Button
            variant="ghost"
            role="combobox"
            aria-expanded={open}
            className="w-full justify-between h-9 px-2 text-sm font-medium hover:bg-muted border border-border rounded-md"
          >
            <div className="flex items-center gap-2 truncate">
              <FolderOpen className="h-3 w-3 text-muted-foreground shrink-0" />
              {activeProject ? (
                <span className="truncate">{activeProject.name}</span>
              ) : (
                <Skeleton className="h-3 w-20" />
              )}
            </div>
            <ChevronsUpDown className="h-3 w-3 opacity-50 shrink-0" />
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-64 p-0" align="start">
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
                    className="flex justify-between items-center relative"
                  >
                    <div className="flex items-center gap-2 w-full">
                      <FolderOpen className="h-4 w-4 text-muted-foreground" />
                      <div className="grow truncate">{project.name}</div>
                      <Check
                        className={cn(
                          "h-4 w-4",
                          activeProject?.id === project.id
                            ? "opacity-100"
                            : "opacity-0",
                        )}
                      />
                    </div>
                  </CommandItem>
                ))}
              </CommandGroup>
              <CommandSeparator />
              <CommandGroup>
                <CommandItem onSelect={handleCreateProjectClick}>
                  <div className="flex items-center gap-2 w-full">
                    <GoPlus className="h-4 w-4" />
                    <span>Create Project</span>
                  </div>
                </CommandItem>
              </CommandGroup>
            </CommandList>
          </Command>
        </PopoverContent>
      </Popover>

      <CreateProjectDialog
        onProjectCreated={reloadActiveProject}
        openDialog={openCreateDialog}
        setOpenDialog={setOpenCreateDialog}
      />
    </>
  );
};
