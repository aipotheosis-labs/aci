"use client";

import { AppMultiSelector } from "./setting-app-selector";
import { FunctionMultiSelector } from "./setting-function-selector";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { LinkAccountOwnerIdSelector } from "./setting-linked-account-owner-id-selector";
import { AgentSelector } from "./setting-agent-selector";
import { Message } from "ai";
import { useEffect } from "react";
import { useAgentStore } from "@/lib/store/agent";
import { toast } from "sonner";
import { useMetaInfo } from "@/components/context/metainfo";
import { useShallow } from "zustand/react/shallow";
interface SettingsSidebarProps {
  status: string;
  setMessages: (messages: Message[]) => void;
}

export function SettingsSidebar({ status, setMessages }: SettingsSidebarProps) {
  const {
    initializeFromProject,
    fetchLinkedAccounts,
    fetchApps,
    fetchAppFunctions,
    getApiKey,
  } = useAgentStore(
    useShallow((state) => ({
      initializeFromProject: state.initializeFromProject,
      fetchLinkedAccounts: state.fetchLinkedAccounts,
      fetchApps: state.fetchApps,
      fetchAppFunctions: state.fetchAppFunctions,
      getApiKey: state.getApiKey,
    })),
  );
  const { activeProject } = useMetaInfo();

  useEffect(() => {
    if (!activeProject) return;

    const initializeData = async () => {
      try {
        initializeFromProject(activeProject);
        const apiKey = getApiKey(activeProject);
        // Initialize settings data (agents, linked accounts, apps, app functions)
        await fetchLinkedAccounts(apiKey);
        await fetchApps(apiKey);
        await fetchAppFunctions(apiKey);
      } catch (error) {
        console.error("Error initializing data:", error);
        toast.error("Failed to initialize data");
      }
    };

    initializeData();
  }, [
    activeProject,
    initializeFromProject,
    fetchLinkedAccounts,
    fetchApps,
    fetchAppFunctions,
    getApiKey,
  ]);
  return (
    <Card className="w-full border-none shadow-none h-full">
      <CardHeader>
        <CardTitle className="font-bold">Playground Settings</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          <AgentSelector status={status} setMessages={setMessages} />
          <LinkAccountOwnerIdSelector
            status={status}
            setMessages={setMessages}
          />
          <AppMultiSelector />
          <FunctionMultiSelector />
        </div>
      </CardContent>
    </Card>
  );
}
