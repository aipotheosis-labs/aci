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
import { useShallow } from "zustand/react/shallow";
interface LinkAccountOwnerIdSelectorProps {
  status: string;
  setMessages: (messages: Message[]) => void;
}

export function LinkAccountOwnerIdSelector({
  status,
  setMessages,
}: LinkAccountOwnerIdSelectorProps) {
  const {
    getUniqueLinkedAccounts,
    selectedLinkedAccountOwnerId,
    setSelectedLinkedAccountOwnerId,
    setSelectedApps,
    setSelectedFunctions,
  } = useAgentStore(
    useShallow((state) => ({
      getUniqueLinkedAccounts: state.getUniqueLinkedAccounts,
      selectedLinkedAccountOwnerId: state.selectedLinkedAccountOwnerId,
      setSelectedLinkedAccountOwnerId: state.setSelectedLinkedAccountOwnerId,
      setSelectedApps: state.setSelectedApps,
      setSelectedFunctions: state.setSelectedFunctions,
      linkedAccounts: state.linkedAccounts,
    })),
  );

  const resetSelectedLinkedAccountOwnerId = (value: string) => {
    setSelectedLinkedAccountOwnerId(value);
    setMessages([]);
    setSelectedApps([]);
    setSelectedFunctions([]);
  };
  const linkedAccounts = getUniqueLinkedAccounts();

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
        value={selectedLinkedAccountOwnerId}
        onValueChange={resetSelectedLinkedAccountOwnerId}
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
