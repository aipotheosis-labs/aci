"use client";

import { Check, ChevronsUpDown, Trash2, Edit2 } from "lucide-react";

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
import { useEffect, useState, useRef } from "react";
import { Skeleton } from "@/components/ui/skeleton";
import { useMetaInfo } from "@/components/context/metainfo";
import { GoPlus } from "react-icons/go";
import { deleteProject, createProject, updateProject } from "@/lib/api/project";
import { toast } from "sonner";
import { Input } from "@/components/ui/input";

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
  const [editingProject, setEditingProject] = useState<string | null>(null);
  const [editedName, setEditedName] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    setProjectSelectOptions(
      projects.map((p) => ({
        value: p.id,
        label: p.name,
      })),
    );
  }, [projects]);

  const handleDeleteProject = async (
    projectId: string,
    e?: React.MouseEvent,
  ) => {
    if (e) {
      e.stopPropagation();
    }

    // Prevent deleting the last project
    if (projects.length <= 1) {
      toast.error("Cannot delete the last project");
      return;
    }

    if (
      !confirm(
        "Are you sure you want to delete this project?\n\n" +
          "This will also delete all related data:\n" +
          "- All agents\n" +
          "- All app configurations\n" +
          "- All linked accounts\n\n" +
          "This action cannot be undone.",
      )
    ) {
      return;
    }

    try {
      await deleteProject(accessToken, projectId);
      toast.success("Project deleted successfully");
      await reloadActiveProject();
    } catch (error) {
      console.error("Failed to delete project:", error);
      toast.error("Failed to delete project");
    }
  };

  const handleEditProject = (
    projectId: string,
    projectName: string,
    e?: React.MouseEvent,
  ) => {
    if (e) {
      e.stopPropagation();
    }

    setEditingProject(projectId);
    setEditedName(projectName);
    setTimeout(() => {
      if (inputRef.current) {
        inputRef.current.focus();
        inputRef.current.select();
      }
    }, 50);
  };

  const handleCreateProject = async () => {
    try {
      const newProject = await createProject(
        accessToken,
        "New Project",
        activeOrg.orgId,
      );
      await reloadActiveProject();
      setOpen(true); // Keep the dropdown open

      // Set the new project to editing mode
      setTimeout(() => {
        handleEditProject(newProject.id, "New Project");
      }, 100);
    } catch (error) {
      console.error("Failed to create project:", error);
      toast.error("Failed to create project");
    }
  };

  const handleUpdateProjectName = async (projectId: string) => {
    if (!editedName.trim()) {
      toast.error("Project name cannot be empty");
      return;
    }

    try {
      await updateProject(accessToken, projectId, editedName);
      await reloadActiveProject();
      setEditingProject(null);
    } catch (error) {
      console.error("Failed to update project name:", error);
      toast.error("Failed to update project name");
    }
  };

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
                    if (editingProject === option.value) {
                      return; // Don't select when editing
                    }
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
                  {editingProject === option.value ? (
                    <Input
                      ref={inputRef}
                      value={editedName}
                      onChange={(e) => setEditedName(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter") {
                          handleUpdateProjectName(option.value);
                        } else if (e.key === "Escape") {
                          setEditingProject(null);
                        }
                      }}
                      onBlur={() => handleUpdateProjectName(option.value)}
                      onClick={(e) => e.stopPropagation()}
                      className="h-6 px-0 py-0 border-none shadow-none focus-visible:ring-0 focus-visible:ring-offset-0 w-full bg-transparent"
                      autoFocus
                    />
                  ) : (
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
                        {projects.length > 1 && (
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-6 w-6 opacity-70 hover:opacity-100 text-destructive"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleDeleteProject(option.value);
                            }}
                          >
                            <Trash2 size={14} />
                          </Button>
                        )}
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-6 w-6 opacity-70 hover:opacity-100"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleEditProject(option.value, option.label);
                          }}
                        >
                          <Edit2 size={14} />
                        </Button>
                      </div>
                    </div>
                  )}
                </CommandItem>
              ))}
            </CommandGroup>
            <CommandSeparator />
            <CommandGroup>
              <CommandItem onSelect={handleCreateProject}>
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
  );
};
