import { useRef, useCallback, useState, useLayoutEffect } from "react";
import type { ToolInvocation } from "ai";
import { useDebounceCallback } from "usehooks-ts";
import { executeFunction } from "@/lib/api/appfunction";

type UseToolExecutionProps = {
  toolInvocation: ToolInvocation;
  addToolResult: ({
    toolCallId,
    result,
  }: {
    toolCallId: string;
    result: object;
  }) => void;
  linkedAccountOwnerId: string;
  apiKey: string;
};

export const useToolExecution = ({
  toolInvocation,
  addToolResult,
  linkedAccountOwnerId,
  apiKey,
}: UseToolExecutionProps) => {
  const { args, toolName } = toolInvocation;
  const hasStartedChecking = useRef<Set<string>>(new Set());
  const [error, setError] = useState<string | null>(null);

  const executeToolCallback = useCallback(async () => {
    // If the tool has already been executed, don't execute it again
    if (hasStartedChecking.current.has(toolInvocation.toolCallId)) {
      return;
    }
    hasStartedChecking.current.add(toolInvocation.toolCallId);
    setError(null);

    try {
      const result = await executeFunction(
        toolName,
        {
          function_input: args as Record<string, unknown>,
          linked_account_owner_id: linkedAccountOwnerId,
        },
        apiKey,
      );

      addToolResult({
        toolCallId: toolInvocation.toolCallId,
        result,
      });
    } catch (error) {
      console.error("Error in tool execution:", error);
      setError(
        error instanceof Error ? error.message : "An unexpected error occurred",
      );
    } finally {
      hasStartedChecking.current.delete(toolInvocation.toolCallId);
    }
  }, [
    toolInvocation.toolCallId,
    toolName,
    args,
    addToolResult,
    linkedAccountOwnerId,
    apiKey,
  ]);

  const debouncedExecute = useDebounceCallback(executeToolCallback, 1000);

  useLayoutEffect(() => {
    debouncedExecute();
    return () => {
      debouncedExecute.cancel();
    };
  }, [debouncedExecute]);

  return {
    error,
  };
};
