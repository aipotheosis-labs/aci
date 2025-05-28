import { Agent } from "@/lib/types/project";
import { useAgentColumns } from "@/components/apps/useAgentColumns";
import { EnhancedDataTable } from "@/components/ui-extensions/enhanced-data-table/data-table";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { DialogFooter } from "@/components/ui/dialog";
import { RowSelectionState } from "@tanstack/react-table";
import * as z from "zod";
import { useMetaInfo } from "@/components/context/metainfo";
import { useUpdateAgent } from "@/hooks/use-agent";
import { toast } from "sonner";
import { useEffect, useState } from "react";

// Form schema for agent selection
export const agentSelectFormSchema = z.object({
  agents: z.array(z.string()).optional(),
});

export type AgentSelectFormValues = z.infer<typeof agentSelectFormSchema>;

interface AgentSelectionStepProps {
  onNext: () => void;
  appName: string;
  isDialogOpen: boolean;
}

export function AgentSelectionStep({
  onNext,
  appName,
  isDialogOpen,
}: AgentSelectionStepProps) {
  const [selectedAgentIds, setSelectedAgentIds] = useState<RowSelectionState>(
    {},
  );
  const { reloadActiveProject, activeProject } = useMetaInfo();
  const columns = useAgentColumns();
  const { mutateAsync: updateAgentMutation, isPending: isUpdatingAgent } =
    useUpdateAgent();

  useEffect(() => {
    if (isDialogOpen && activeProject?.agents) {
      const initialSelection: RowSelectionState = {};
      activeProject.agents.forEach((agent: Agent) => {
        if (agent.id) {
          initialSelection[agent.id] = true;
        }
      });
      setSelectedAgentIds(initialSelection);
    }
  }, [isDialogOpen, activeProject]);

  const handleNext = async () => {
    if (Object.keys(selectedAgentIds).length === 0) {
      onNext();
      return;
    }
    try {
      const agentsToUpdate = activeProject.agents.filter(
        (agent) => agent.id && selectedAgentIds[agent.id],
      );

      for (const agent of agentsToUpdate) {
        const allowedApps = new Set(agent.allowed_apps);
        allowedApps.add(appName);
        await updateAgentMutation({
          id: agent.id,
          data: {
            allowed_apps: Array.from(allowedApps),
          },
          noreload: true,
        });
      }
      toast.success("agents updated successfully");
      await reloadActiveProject();
      onNext();
    } catch (error) {
      console.error("agents updated app failed:", error);
      toast.error("agents updated app failed");
    }
  };

  const agents = activeProject?.agents || [];

  return (
    <div className="space-y-2">
      {agents.length > 0 ? (
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-medium">Selected Agents</h3>
            <Badge
              variant="secondary"
              className="flex items-center gap-1 px-2 py-1 text-xs"
            >
              Selected {Object.keys(selectedAgentIds).length} Agents
            </Badge>
          </div>
          <EnhancedDataTable
            columns={columns}
            data={agents}
            searchBarProps={{ placeholder: "search agent..." }}
            rowSelectionProps={{
              rowSelection: selectedAgentIds,
              onRowSelectionChange: setSelectedAgentIds,
              getRowId: (row) => row.id,
            }}
          />
        </div>
      ) : (
        <div className="flex items-center justify-center p-8 border rounded-md">
          <p className="text-muted-foreground">No Available Agents</p>
        </div>
      )}

      <DialogFooter>
        <Button type="button" onClick={handleNext} disabled={isUpdatingAgent}>
          {isUpdatingAgent ? "Confirming..." : "Confirm"}
        </Button>
      </DialogFooter>
    </div>
  );
}
