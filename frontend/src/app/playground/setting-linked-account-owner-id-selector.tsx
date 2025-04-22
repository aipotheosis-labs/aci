"use client";

import {
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem,
} from "@/components/ui/select";
import { useAgentStore } from "@/lib/store/agent";
import { Message } from "ai";
import {
  Tooltip,
  TooltipTrigger,
  TooltipContent,
} from "@/components/ui/tooltip";
import { BsQuestionCircle } from "react-icons/bs";
interface LinkAccountOwnerIdSelectorProps {
  linkedAccounts: { linked_account_owner_id: string }[];
  status: string;
  setMessages: (messages: Message[]) => void;
}

export function LinkAccountOwnerIdSelector({
  linkedAccounts,
  status,
  setMessages,
}: LinkAccountOwnerIdSelectorProps) {
  const { linkedAccountOwnerId, setLinkedAccountOwnerId } = useAgentStore();

  const resetLinkedAccountOwnerId = (value: string) => {
    setLinkedAccountOwnerId(value);
    setMessages([]);
  };

  return (
    <div className="space-y-2">
      <Tooltip>
        <div className="flex items-center gap-2">
          <h3 className="text-sm font-medium">Linked Account Owner ID</h3>
          <TooltipTrigger asChild>
            <BsQuestionCircle className="h-4 w-4 text-muted-foreground" />
          </TooltipTrigger>
        </div>
        <TooltipContent>
          <p>Select which user you want to test the agent as.</p>
        </TooltipContent>
      </Tooltip>
      <Select
        value={linkedAccountOwnerId}
        onValueChange={resetLinkedAccountOwnerId}
        disabled={status !== "ready"}
      >
        <SelectTrigger className="w-full">
          <SelectValue placeholder="Select a Linked Account Owner" />
        </SelectTrigger>
        <SelectContent>
          {linkedAccounts.map((account) => (
            <SelectItem
              key={account.linked_account_owner_id}
              value={account.linked_account_owner_id}
            >
              {account.linked_account_owner_id}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}
