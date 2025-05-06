"use client";

import { useMetaInfo } from "@/components/context/metainfo";
import { useChat } from "@ai-sdk/react";
import { useAgentStore } from "@/lib/store/agent";
import { executeFunction, searchFunctions } from "@/lib/api/appfunction";
import { SettingsSidebar } from "./playground-settings";
import { ChatInput } from "./chat-input";
import { Messages } from "./messages";
import { useShallow } from "zustand/react/shallow";
import { BetaAlert } from "@/components/playground/beta-alert";
const Page = () => {
  const { activeProject } = useMetaInfo();

  // Use selective state with useShallow to prevent unnecessary re-renders
  const {
    selectedApps,
    selectedFunctions,
    selectedLinkedAccountOwnerId,
    getApiKey,
  } = useAgentStore(
    useShallow((state) => ({
      selectedApps: state.selectedApps,
      selectedFunctions: state.selectedFunctions,
      selectedLinkedAccountOwnerId: state.selectedLinkedAccountOwnerId,
      getApiKey: state.getApiKey,
    })),
  );

  // Only compute this when activeProject changes
  const apiKey = activeProject ? getApiKey(activeProject) : "";

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
      linked_account_owner_id: selectedLinkedAccountOwnerId,
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
            linked_account_owner_id: selectedLinkedAccountOwnerId,
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
            linked_account_owner_id: selectedLinkedAccountOwnerId,
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

  if (!activeProject) {
    console.warn("No active project");
    return <div>No project selected</div>;
  }

  return (
    <div className="flex flex-grow h-[calc(100vh-6rem)]">
      {/* Left part - Chat area */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <BetaAlert />
        <Messages messages={messages} status={status} />
        <ChatInput
          input={input}
          handleInputChange={handleInputChange}
          handleSubmit={handleSubmit}
          status={status}
          linkedAccountOwnerId={selectedLinkedAccountOwnerId}
        />
      </div>

      {/* Right part - Settings sidebar */}
      <div className="w-80 border-l">
        <SettingsSidebar status={status} setMessages={setMessages} />
      </div>
    </div>
  );
};

export default Page;
