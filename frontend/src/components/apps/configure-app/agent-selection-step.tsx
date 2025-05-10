import { Agent } from "@/lib/types/project";
import { useAgentColumns } from "@/components/apps/useAgentColumns";
import { EnhancedDataTable } from "@/components/ui-extensions/enhanced-data-table/data-table";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { DialogFooter } from "@/components/ui/dialog";
import { RowSelectionState, OnChangeFn } from "@tanstack/react-table";
import * as z from "zod";

// Form schema for agent selection
export const agentSelectFormSchema = z.object({
  agents: z.array(z.string()).optional(),
});

export type AgentSelectFormValues = z.infer<typeof agentSelectFormSchema>;

interface AgentSelectionStepProps {
  agents: Agent[];
  rowSelection: RowSelectionState;
  onRowSelectionChange: OnChangeFn<RowSelectionState>;
  onNext: () => void;
  isLoading: boolean;
}

export function AgentSelectionStep({
  agents,
  rowSelection,
  onRowSelectionChange,
  onNext,
  isLoading,
}: AgentSelectionStepProps) {
  const columns = useAgentColumns();

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
              Selected {Object.keys(rowSelection).length} Agents
            </Badge>
          </div>
          <EnhancedDataTable
            columns={columns}
            data={agents}
            searchBarProps={{ placeholder: "search agent..." }}
            rowSelectionProps={{
              rowSelection: rowSelection,
              onRowSelectionChange: onRowSelectionChange,
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
        <Button type="button" onClick={onNext} disabled={isLoading}>
          {isLoading ? "Confirming..." : "Confirm"}
        </Button>
      </DialogFooter>
    </div>
  );
}
