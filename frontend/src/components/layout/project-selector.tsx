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
import { CreateProjectDialog } from "@/components/project/create-project-dialog";

interface ProjectSelectOption {
  value: string; // project id
  label: string; // project name
}

export const ProjectSelector = () => {
  const {
    projects,
    activeProject,
    setActiveProject,
    accessToken,
    reloadActiveProject,
    activeOrg,
  } = useMetaInfo();
  const [projectSelectOptions, setProjectSelectOptions] = useState<
    ProjectSelectOption[]
  >([]);
  const [open, setOpen] = useState(false);
  const [openCreateDialog, setOpenCreateDialog] = useState(false);

  useEffect(() => {
    setProjectSelectOptions(
      projects.map((p) => ({
        value: p.id,
        label: p.name,
      })),
    );
  }, [projects]);

  const handleCreateProjectClick = () => {
    setOpen(false);
    setOpenCreateDialog(true);
  };

  return (
    <>
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
                    className="flex justify-between items-center relative"
                  >
                    <div className="flex justify-between items-center w-full">
                      <div className="flex-grow">{option.label}</div>
                      <div className="flex items-center">
                        <Check
                          className={cn(
                            "mr-2",
                            activeProject?.id === option.value
                              ? "opacity-100"
                              : "opacity-0",
                          )}
                        />
                      </div>
                    </div>
                  </CommandItem>
                ))}
              </CommandGroup>
              <CommandSeparator />
              <CommandGroup>
                <CommandItem onSelect={handleCreateProjectClick}>
                  <div className="flex items-center w-full">
                    <GoPlus className="mr-2" />
                    <span>Create Project</span>
                  </div>
                </CommandItem>
              </CommandGroup>
            </CommandList>
          </Command>
        </PopoverContent>
      </Popover>

      <CreateProjectDialog
        accessToken={accessToken}
        orgId={activeOrg.orgId}
        onProjectCreated={reloadActiveProject}
        openDialog={openCreateDialog}
        setOpenDialog={setOpenCreateDialog}
        trigger={<span style={{ display: "none" }} />}
      />
    </>
  );
};
