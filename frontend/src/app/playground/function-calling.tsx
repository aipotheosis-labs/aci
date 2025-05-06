import { useToolExecution } from "@/hooks/use-tool-execution";
import type { ToolInvocation } from "ai";

type FunctionCallingProps = {
  toolInvocation: ToolInvocation;
  linkedAccountOwnerId: string;
  apiKey: string;
  addToolResult: ({
    toolCallId,
    result,
  }: {
    toolCallId: string;
    result: object;
  }) => void;
};

export function FunctionCalling({
  toolInvocation,
  linkedAccountOwnerId,
  apiKey,
  addToolResult,
}: FunctionCallingProps) {
  const { toolName } = toolInvocation;

  const { error } = useToolExecution({
    toolInvocation,
    addToolResult,
    linkedAccountOwnerId,
    apiKey,
  });

  if (error) {
    return <div>Function Calling Error: {error}</div>;
  }

  return (
    <div className="flex items-center space-x-2 border border-gray-200 rounded-md p-2">
      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-900"></div>
      <span>Function Calling: {toolName}</span>
    </div>
  );
}
