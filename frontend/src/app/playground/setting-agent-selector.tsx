"use client";

import {
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem,
} from "@/components/ui/select";
import { useAgentStore } from "@/lib/store/agent";
import { Agent } from "@/lib/types/project";
import { Message } from "ai";
import {
  Tooltip,
  TooltipTrigger,
  TooltipContent,
} from "@/components/ui/tooltip";
import { BsQuestionCircle } from "react-icons/bs";
interface AgentSelectorProps {
  agents: Agent[];
  setMessages: (messages: Message[]) => void;
}

export function AgentSelector({ agents, setMessages }: AgentSelectorProps) {
  const { selectedAgent, setSelectedAgent, setAllowedApps } = useAgentStore();
  const hasAgents = agents && agents.length > 0;

  const handleAgentChange = (value: string) => {
    setSelectedAgent(value);
    setMessages([]);

    // Find the selected agent and update allowedApps
    const selectedAgentData = agents.find((agent) => agent.id === value);
    if (selectedAgentData) {
      setAllowedApps(selectedAgentData.allowed_apps || []);
    } else {
      setAllowedApps([]);
    }
  };

  return (
    <div className="space-y-2">
      <Tooltip>
        <div className="flex items-center gap-2">
          <h3 className="text-sm font-medium">Agent</h3>
          <TooltipTrigger asChild>
            <BsQuestionCircle className="h-4 w-4 text-muted-foreground" />
          </TooltipTrigger>
        </div>
        <TooltipContent>
          <p>
            Select the agent you want to test, create new ones in manage
            project.
          </p>
        </TooltipContent>
      </Tooltip>

      {!hasAgents ? (
        <div className="text-sm text-muted-foreground p-2 border rounded-md">
          No agents available
        </div>
      ) : (
        <Select
          value={selectedAgent}
          onValueChange={handleAgentChange}
          disabled={true}
        >
          <SelectTrigger className="w-full" aria-label="Select an agent">
            <SelectValue placeholder="Select an Agent" />
          </SelectTrigger>
          <SelectContent>
            {agents.map((agent) => (
              <SelectItem key={agent.id} value={agent.id}>
                {agent.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      )}
    </div>
  );
}
