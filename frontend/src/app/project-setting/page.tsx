"use client";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
// import { Switch } from "@/components/ui/switch";
import { CreateAgentForm } from "@/components/project/create-agent-form";
import { Separator } from "@/components/ui/separator";
import { IdDisplay } from "@/components/apps/id-display";
// import { RiTeamLine } from "react-icons/ri";
import { MdAdd } from "react-icons/md";
import { BsQuestionCircle } from "react-icons/bs";
import { Check, Edit2 } from "lucide-react";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { useCallback, useState, useEffect } from "react";
import { useAgentsTableColumns } from "@/components/project/useAgentsTableColumns";
import { EnhancedDataTable } from "@/components/ui-extensions/enhanced-data-table/data-table";
import { Agent } from "@/lib/types/project";
import { toast } from "sonner";
import { useMetaInfo } from "@/components/context/metainfo";
import { useAppConfigs } from "@/hooks/use-app-config";
import { useCreateAgent, useDeleteAgent } from "@/hooks/use-agent";
import { updateProject } from "@/lib/api/project";
import { DeleteProjectDialog } from "@/components/project/delete-project-dialog";

export default function ProjectSettingPage() {
  const { activeProject } = useMetaInfo();
  const { data: appConfigs = [], isPending: isConfigsPending } =
    useAppConfigs();
  const [projectName, setProjectName] = useState(activeProject.name);
  const [isEditingName, setIsEditingName] = useState(false);
  const { accessToken, reloadActiveProject } = useMetaInfo();

  // Update state when active project changes
  useEffect(() => {
    setProjectName(activeProject.name);
    setIsEditingName(false);
  }, [activeProject]);

  const handleSaveProjectName = async () => {
    if (!projectName.trim()) {
      toast.error("Project name cannot be empty");
      return;
    }

    // Only update if the name has actually changed
    if (projectName === activeProject.name) {
      setIsEditingName(false);
      return;
    }

    try {
      await updateProject(accessToken, activeProject.id, projectName);
      await reloadActiveProject();
      setIsEditingName(false);
      toast.success("Project name updated");
    } catch (error) {
      console.error("Failed to update project name:", error);
      toast.error("Failed to update project name");
    }
  };

  const { mutateAsync: createAgentMutation } = useCreateAgent();
  const { mutateAsync: deleteAgentMutation } = useDeleteAgent();

  const handleDeleteAgent = useCallback(
    async (agentId: string) => {
      try {
        if (activeProject.agents.length <= 1) {
          toast.error(
            "Failed to delete agent. You must keep at least one agent in the project.",
          );
          return;
        }

        await deleteAgentMutation(agentId);
      } catch (error) {
        console.error("Error deleting agent:", error);
      }
    },
    [activeProject, deleteAgentMutation],
  );

  const agentTableColumns = useAgentsTableColumns(
    activeProject.id,
    handleDeleteAgent,
  );

  return (
    <div className="w-full">
      <div className="flex items-center justify-between m-4">
        <h1 className="text-2xl font-semibold">Project settings</h1>
        {/* <Button
          variant="outline"
          className="text-red-500 hover:text-red-600 hover:bg-red-50"
        >
          Delete project
        </Button> */}
      </div>
      <Separator />

      <div className="px-4 py-6 space-y-6">
        {/* Project Name Section */}
        <div className="flex flex-row">
          <div className="flex flex-col items-left w-80">
            <label className="font-semibold">Project Name</label>
            <p className="text-sm text-muted-foreground">
              Change the name of the project
            </p>
          </div>
          <div className="flex items-center gap-2">
            <div className="relative">
              <Input
                value={projectName}
                onChange={(e) => setProjectName(e.target.value)}
                className="w-96"
                disabled={!isEditingName}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    handleSaveProjectName();
                  } else if (e.key === "Escape") {
                    setIsEditingName(false);
                    setProjectName(activeProject.name);
                  }
                }}
              />
            </div>
            {isEditingName ? (
              <Button
                size="sm"
                variant="ghost"
                onClick={handleSaveProjectName}
                className="h-8 w-8 p-0"
              >
                <Check className="h-4 w-4" />
              </Button>
            ) : (
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    onClick={() => setIsEditingName(true)}
                    className="h-8 w-8 p-0"
                  >
                    <Edit2 className="h-4 w-4" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>
                  <p>Click to edit project name</p>
                </TooltipContent>
              </Tooltip>
            )}
          </div>
        </div>

        <Separator />

        {/* Project ID Section */}
        <div className="flex flex-row">
          <div className="flex flex-col items-left w-80">
            <div className="flex items-center gap-2">
              <label className="font-semibold">Project ID</label>
              <Tooltip>
                <TooltipTrigger asChild>
                  <span className="cursor-pointer">
                    <BsQuestionCircle className="h-4 w-4 text-muted-foreground" />
                  </span>
                </TooltipTrigger>
                <TooltipContent side="top">
                  <p className="text-xs">A project can have multiple agents.</p>
                </TooltipContent>
              </Tooltip>
            </div>
          </div>
          <div className="flex items-center px-2">
            <IdDisplay id={activeProject.id} dim={false} />
          </div>
        </div>

        <Separator />

        {/* Team Section */}
        {/* <div className="flex flex-row">
          <div className="flex flex-col items-left w-80">
            <label className="font-semibold">Team</label>
            <p className="text-sm text-muted-foreground">
              Easily manage your team
            </p>
          </div>
          <div>
            <Button variant="outline">
              <RiTeamLine />
              Manage Members
            </Button>
          </div>
        </div>

        <Separator /> */}

        {/* Agent Section */}
        <div className="flex flex-row">
          <div className="flex flex-col items-left w-80">
            <div className="flex items-center gap-2">
              <label className="font-semibold">Agent</label>
              <Tooltip>
                <TooltipTrigger asChild>
                  <span className="cursor-pointer">
                    <BsQuestionCircle className="h-4 w-4 text-muted-foreground" />
                  </span>
                </TooltipTrigger>
                <TooltipContent side="top">
                  <p className="text-xs">
                    Each agent has a unique API key that can be used to access a
                    different set of tools/apps configured for the project.
                  </p>
                </TooltipContent>
              </Tooltip>
            </div>
            <p className="text-sm text-muted-foreground">
              Add and manage agents
            </p>
          </div>
          <div className="flex items-center justify-between w-96">
            {/* <div className="flex items-center gap-2">
              <Switch checked={hasAgents} />
              <span className="text-sm">Enable</span>
            </div> */}
            <div className="flex items-center gap-2">
              <CreateAgentForm
                title="Create Agent"
                validAppNames={appConfigs.map(
                  (appConfig) => appConfig.app_name,
                )}
                appConfigs={appConfigs}
                onSubmit={async (values) => {
                  try {
                    await createAgentMutation(values);
                  } catch (error) {
                    console.error("Error creating agent:", error);
                  }
                }}
              >
                <Button variant="outline" disabled={isConfigsPending}>
                  <MdAdd />
                  Create Agent
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <span className="cursor-pointer">
                        <BsQuestionCircle className="h-4 w-4 text-muted-foreground" />
                      </span>
                    </TooltipTrigger>
                    <TooltipContent side="top">
                      <p className="text-xs">
                        Create a new agent API key to access applications
                        configured for this project.
                      </p>
                    </TooltipContent>
                  </Tooltip>
                </Button>
              </CreateAgentForm>
            </div>
          </div>
        </div>

        {activeProject.agents && activeProject.agents.length > 0 && (
          <EnhancedDataTable
            columns={agentTableColumns}
            data={activeProject.agents as Agent[]}
            defaultSorting={[{ id: "name", desc: true }]}
            searchBarProps={{ placeholder: "Search agents..." }}
          />
        )}
        {/* Delete Project Section */}
        <div className="mt-8">
          <h2 className="text-lg font-semibold mb-4">Danger Zone</h2>
          <div className="border border-red-200 rounded-md bg-red-50">
            <div className="p-4 flex items-center justify-between">
              <div>
                <h3 className="font-medium">Delete this project</h3>
                <p className="text-sm text-gray-500 mt-1">
                  Once you delete a project, there is no going back. This action
                  permanently deletes the project and all related data.
                </p>
              </div>
              <DeleteProjectDialog
                accessToken={accessToken}
                projectId={activeProject.id}
                projectName={activeProject.name}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
