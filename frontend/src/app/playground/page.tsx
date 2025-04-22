"use client";

import { useMetaInfo } from "@/components/context/metainfo";
import { useChat } from "@ai-sdk/react";
import { useState, useEffect } from "react";
import { toast } from "sonner";
import { useAgentStore } from "@/lib/store/agent";
import { executeFunction, searchFunctions } from "@/lib/api/appfunction";
import { getAllLinkedAccounts } from "@/lib/api/linkedaccount";
import type { LinkedAccount } from "@/lib/types/linkedaccount";
import { SettingsSidebar } from "./playground-settings";
import { Agent } from "@/lib/types/project";
import { ChatInput } from "./chat-input";
import { Messages } from "./messages";

const Page = () => {
  const { activeProject } = useMetaInfo();
  const [linkedAccounts, setLinkedAccounts] = useState<LinkedAccount[]>([]);
  const [agents, setAgents] = useState<Agent[]>([]);
  const {
    selectedApps,
    selectedFunctions,
    linkedAccountOwnerId,
    setLinkedAccountOwnerId,
    setSelectedAgent,
    setAllowedApps,
    getApiKey,
  } = useAgentStore();

  const apiKey = getApiKey(activeProject);

  const {
    messages,
    input,
    handleSubmit,
    handleInputChange,
    status,
    addToolResult,
    setMessages,
  } = useChat({
    api: `${process.env.NEXT_PUBLIC_API_URL}/v1/agent/chat`,
    headers: {
      "Content-Type": "application/json",
      "x-api-key": apiKey,
    },
    body: {
      linked_account_owner_id: linkedAccountOwnerId,
      selected_apps: selectedApps,
      selected_functions: selectedFunctions,
    },
    streamProtocol: "data",
    maxSteps: 3,
    onFinish: (message) => {
      console.log(message);
    },
    onToolCall: async ({ toolCall }) => {
      // TODO: Human in the loop
      console.log("tool call", toolCall);

      let result;
      // when the tool call name is "ACI_SEARCH_FUNCTIONS"
      if (toolCall.toolName === "ACI_SEARCH_FUNCTIONS") {
        result = await searchFunctions(
          toolCall.args as Record<string, unknown>,
          apiKey,
        );
        addToolResult({
          toolCallId: toolCall.toolCallId,
          result: result,
        });
      } else if (toolCall.toolName === "ACI_EXECUTE_FUNCTION") {
        result = await executeFunction(
          toolCall.toolName,
          {
            function_input: toolCall.args as Record<string, unknown>,
            linked_account_owner_id: linkedAccountOwnerId,
          },
          apiKey,
        );
        addToolResult({
          toolCallId: toolCall.toolCallId,
          result: result,
        });
      } else {
        result = await executeFunction(
          toolCall.toolName,
          {
            function_input: toolCall.args as Record<string, unknown>,
            linked_account_owner_id: linkedAccountOwnerId,
          },
          apiKey,
        );
        addToolResult({
          toolCallId: toolCall.toolCallId,
          result: result,
        });
      }
    },
  });

  useEffect(() => {
    const fetchLinkedAccounts = async () => {
      if (!activeProject) return;
      try {
        const accounts = await getAllLinkedAccounts(apiKey);
        const uniqueAccounts = Array.from(
          new Map(
            accounts.map((account) => [
              account.linked_account_owner_id,
              account,
            ]),
          ).values(),
        );
        setLinkedAccounts(uniqueAccounts);
        if (uniqueAccounts.length > 0 && !linkedAccountOwnerId) {
          setLinkedAccountOwnerId(uniqueAccounts[0].linked_account_owner_id);
        }
      } catch (error) {
        console.error("Failed to fetch linked accounts:", error);
        toast.error("Failed to fetch linked accounts");
      }
    };

    fetchLinkedAccounts();
  }, [activeProject, apiKey, linkedAccountOwnerId, setLinkedAccountOwnerId]);

  useEffect(() => {
    if (activeProject?.agents) {
      setAgents(activeProject.agents);
      // TODO: set the first agent as the selected agent, might need to change this
      setSelectedAgent(activeProject.agents[0].id);
      setAllowedApps(activeProject.agents[0].allowed_apps || []);
    }
  }, [activeProject, setSelectedAgent, setAllowedApps]);

  if (!activeProject) {
    console.warn("No active project");
    return <div>No project selected</div>;
  }

  return (
    <div className="flex flex-grow h-[calc(100vh-6rem)]">
      {/* Left part - Chat area */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <Messages messages={messages} status={status} />
        <ChatInput
          input={input}
          handleInputChange={handleInputChange}
          handleSubmit={handleSubmit}
          status={status}
          linkedAccountOwnerId={linkedAccountOwnerId}
        />
      </div>

      {/* Right part - Settings sidebar */}
      <div className="w-80 border-l">
        <SettingsSidebar
          linkedAccounts={linkedAccounts}
          agents={agents}
          status={status}
          setMessages={setMessages}
        />
      </div>
    </div>
  );
};

export default Page;
