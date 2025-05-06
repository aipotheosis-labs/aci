"use client";

import { useMetaInfo } from "@/components/context/metainfo";
import { useChat } from "@ai-sdk/react";
import { useAgentStore } from "@/lib/store/agent";
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
    stop,
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
  });

  const handleAddToolResult = ({
    toolCallId,
    result,
  }: {
    toolCallId: string;
    result: object;
  }) => {
    addToolResult({ toolCallId, result });
  };

  if (!activeProject) {
    console.warn("No active project");
    return <div>No project selected</div>;
  }

  return (
    <div className="flex flex-grow h-[calc(100vh-6rem)]">
      {/* Left part - Chat area */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <BetaAlert />
        <Messages
          messages={messages}
          status={status}
          linkedAccountOwnerId={selectedLinkedAccountOwnerId}
          apiKey={apiKey}
          addToolResult={handleAddToolResult}
        />
        <ChatInput
          input={input}
          setMessages={setMessages}
          stop={stop}
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
