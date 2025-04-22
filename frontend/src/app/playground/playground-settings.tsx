"use client";

import { AppMultiSelector } from "./setting-app-selector";
import { FunctionMultiSelector } from "./setting-function-selector";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { LinkAccountOwnerIdSelector } from "./setting-linked-account-owner-id-selector";
import { AgentSelector } from "./setting-agent-selector";
import { Agent } from "@/lib/types/project";
import { Message } from "ai";

interface SettingsSidebarProps {
  linkedAccounts: { linked_account_owner_id: string }[];
  agents: Agent[];
  status: string;
  setMessages: (messages: Message[]) => void;
}

export function SettingsSidebar({
  linkedAccounts,
  agents,
  status,
  setMessages,
}: SettingsSidebarProps) {
  return (
    <Card className="w-full border-none shadow-none h-full">
      <CardHeader>
        <CardTitle className="font-bold">Playground Settings</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          <AgentSelector
            agents={agents}
            status={status}
            setMessages={setMessages}
          />
          <LinkAccountOwnerIdSelector
            linkedAccounts={linkedAccounts}
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
