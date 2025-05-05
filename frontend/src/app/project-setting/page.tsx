"use client";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
// import { Switch } from "@/components/ui/switch";
import { AgentForm } from "@/components/project/agent-form";
import { createAgent, deleteAgent } from "@/lib/api/agent";
import { Separator } from "@/components/ui/separator";
import { IdDisplay } from "@/components/apps/id-display";
// import { RiTeamLine } from "react-icons/ri";
import { MdAdd } from "react-icons/md";
import { BsQuestionCircle } from "react-icons/bs";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { useCallback, useEffect, useState } from "react";
import { getApiKey } from "@/lib/api/util";
import { useAgentsTableColumns } from "@/components/project/useAgentsTableColumns";
import { EnhancedDataTable } from "@/components/ui-extensions/enhanced-data-table/data-table";
import { Agent } from "@/lib/types/project";
import { toast } from "sonner";
import { useMetaInfo } from "@/components/context/metainfo";
import { AppConfig } from "@/lib/types/appconfig";
import { getAllAppConfigs } from "@/lib/api/appconfig";

export default function ProjectSettingPage() {
  const { accessToken, activeProject, reloadActiveProject } = useMetaInfo();
  const [appConfigs, setAppConfigs] = useState<AppConfig[]>([]);
  const [loading, setLoading] = useState(false);

  const loadAppConfigs = useCallback(async () => {
    const apiKey = getApiKey(activeProject);
    setLoading(true);

    try {
      const configs = await getAllAppConfigs(apiKey);
      setAppConfigs(configs);
    } catch (error) {
      console.error("Error fetching apps:", error);
    } finally {
      setLoading(false);
    }
  }, [activeProject]);

  useEffect(() => {
    loadAppConfigs();
  }, [activeProject, loadAppConfigs]);

  const handleDeleteAgent = useCallback(
    async (agentId: string) => {
      try {
        if (activeProject.agents.length <= 1) {
          toast.error(
            "Failed to delete agent. You must keep at least one agent in the project.",
          );
          return;
        }

        await deleteAgent(activeProject.id, agentId, accessToken);
        await reloadActiveProject();
      } catch (error) {
        console.error("Error deleting agent:", error);
      }
    },
    [activeProject, accessToken, reloadActiveProject],
  );

  const agentTableColumns = useAgentsTableColumns(
    activeProject.id,
    handleDeleteAgent,
    reloadActiveProject,
    reloadActiveProject,
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
          <div>
            <Input
              defaultValue={activeProject.name}
              className="w-96"
              readOnly
            />
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
              <AgentForm
                title="Create Agent"
                validAppNames={appConfigs.map(
                  (appConfig) => appConfig.app_name,
                )}
                appConfigs={appConfigs}
                onRequestRefreshAppConfigs={loadAppConfigs}
                onSubmit={async (values) => {
                  try {
                    await createAgent(
                      activeProject.id,
                      accessToken,
                      values.name,
                      values.description,
                      // TODO: need to create a UI for specifying allowed apps
                      values.allowed_apps,
                      values.custom_instructions,
                    );
                    await reloadActiveProject();
                  } catch (error) {
                    console.error("Error creating agent:", error);
                  }
                }}
              >
                <Button variant="outline" disabled={loading}>
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
              </AgentForm>
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
      </div>
    </div>
  );
}
