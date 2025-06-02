"use client";

import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { BsQuestionCircle } from "react-icons/bs";
import { MdAdd } from "react-icons/md";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { useCallback } from "react";
import { useAgentsTableColumns } from "@/components/project/useAgentsTableColumns";
import { EnhancedDataTable } from "@/components/ui-extensions/enhanced-data-table/data-table";
import { Agent } from "@/lib/types/project";
import { toast } from "sonner";
import { useMetaInfo } from "@/components/context/metainfo";
import { useAppConfigs } from "@/hooks/use-app-config";
import { CreateAgentForm } from "@/components/project/create-agent-form";
import { useCreateAgent, useDeleteAgent } from "@/hooks/use-agent";

export default function AgentsPage() {
  const { activeProject } = useMetaInfo();
  const { data: appConfigs = [], isPending: isConfigsPending } =
    useAppConfigs();

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
        toast.success("Agent deleted successfully");
      } catch (error) {
        console.error("Error deleting agent:", error);
        toast.error("Failed to delete agent");
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
        <div>
          <h1 className="text-2xl font-semibold">Agents</h1>
          <p className="text-sm text-muted-foreground">
            Manage your project agents and their API keys
          </p>
        </div>
        <CreateAgentForm
          title="Create Agent"
          validAppNames={appConfigs.map((appConfig) => appConfig.app_name)}
          appConfigs={appConfigs}
          onSubmit={async (values) => {
            try {
              await createAgentMutation(values);
              toast.success("Agent created successfully");
            } catch (error) {
              console.error("Error creating agent:", error);
              toast.error("Failed to create agent");
            }
          }}
        >
          <Button variant="default" disabled={isConfigsPending}>
            <MdAdd />
            Create Agent
            <Tooltip>
              <TooltipTrigger asChild>
                <span className="cursor-pointer ml-1">
                  <BsQuestionCircle className="h-4 w-4 text-white/70" />
                </span>
              </TooltipTrigger>
              <TooltipContent side="top">
                <p className="text-xs">
                  Create a new agent API key to access applications configured
                  for this project.
                </p>
              </TooltipContent>
            </Tooltip>
          </Button>
        </CreateAgentForm>
      </div>
      <Separator />

      <div className="p-4">
        <div className="mb-4">
          <div className="flex items-center gap-2">
            <p className="text-sm">
              Each agent has a unique API key that can be used to access a
              different set of tools/apps configured for this project.
            </p>
          </div>
        </div>

        {activeProject.agents && activeProject.agents.length > 0 && (
          <EnhancedDataTable
            columns={agentTableColumns}
            data={activeProject.agents as Agent[]}
            defaultSorting={[{ id: "name", desc: false }]}
            searchBarProps={{ placeholder: "Search agents..." }}
          />
        )}
      </div>
    </div>
  );
}
