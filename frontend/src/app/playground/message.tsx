"use client";
import type { UIMessage } from "ai";
import cx from "classnames";
import * as motion from "motion/react-client";
import { AnimatePresence } from "motion/react";
import { memo } from "react";
import { SparklesIcon } from "lucide-react";
import equal from "fast-deep-equal";
import { cn } from "@/lib/utils";
import { MessageReasoning } from "./message-reasoning";
import { FunctionCallingResult } from "./function-calling-result";
import { FunctionCalling } from "./function-calling";
import { Markdown } from "./markdown";

const PurePreviewMessage = ({
  message,
  isLoading,
  linkedAccountOwnerId,
  apiKey,
  addToolResult,
}: {
  message: UIMessage;
  isLoading: boolean;
  linkedAccountOwnerId: string;
  apiKey: string;
  addToolResult: ({
    toolCallId,
    result,
  }: {
    toolCallId: string;
    result: object;
  }) => void;
}) => {
  return (
    <AnimatePresence>
      <motion.div
        data-testid={`message-${message.role}`}
        className="w-full mx-auto max-w-3xl px-4 group/message"
        initial={{ y: 5, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        data-role={message.role}
      >
        <div
          className={cn(
            "flex gap-4 w-full group-data-[role=user]/message:ml-auto group-data-[role=user]/message:max-w-2xl",
            {
              "w-full": true,
              "group-data-[role=user]/message:w-fit": true,
            },
          )}
        >
          {message.role === "assistant" && (
            <div
              className={cn(
                "size-8 flex items-center rounded-full justify-center ring-1 shrink-0 ring-border bg-background",
                {
                  "animate-pulse": isLoading,
                },
              )}
            >
              <div className="translate-y-px">
                <SparklesIcon size={14} />
              </div>
            </div>
          )}

          <div className="flex flex-col gap-4 w-full">
            {message.parts?.map((part, index) => {
              const { type } = part;
              const key = `message-${message.id}-part-${index}`;

              if (type === "reasoning") {
                return (
                  <MessageReasoning
                    key={key}
                    isLoading={isLoading}
                    reasoning={part.reasoning}
                  />
                );
              }

              if (type === "text") {
                return (
                  <div key={key} className="flex flex-row gap-2 items-start">
                    <div
                      data-testid="message-content"
                      className={cn("flex flex-col gap-4", {
                        "bg-zinc-100 px-3 py-2 rounded-xl":
                          message.role === "user",
                      })}
                    >
                      <Markdown isUserMessage={message.role === "user"}>
                        {part.text}
                      </Markdown>
                    </div>
                  </div>
                );
              }

              if (type === "tool-invocation") {
                const { toolInvocation } = part;
                const { toolCallId, state } = toolInvocation;

                if (state === "result") {
                  return (
                    <FunctionCallingResult
                      key={`${toolCallId}-${state}`}
                      toolInvocation={toolInvocation}
                    />
                  );
                }

                if (state === "call") {
                  return (
                    <FunctionCalling
                      key={`${toolCallId}-${state}`}
                      toolInvocation={toolInvocation}
                      linkedAccountOwnerId={linkedAccountOwnerId}
                      apiKey={apiKey}
                      addToolResult={addToolResult}
                    />
                  );
                }
              }
            })}
          </div>
        </div>
      </motion.div>
    </AnimatePresence>
  );
};

export const PreviewMessage = memo(
  PurePreviewMessage,
  (prevProps, nextProps) => {
    if (prevProps.isLoading !== nextProps.isLoading) return false;
    if (prevProps.message.id !== nextProps.message.id) return false;
    if (!equal(prevProps.message.parts, nextProps.message.parts)) return false;

    return true;
  },
);

export const ThinkingMessage = () => {
  const role = "assistant";

  return (
    <motion.div
      data-testid="message-assistant-loading"
      className="w-full mx-auto max-w-3xl px-4 group/message "
      initial={{ y: 5, opacity: 0 }}
      animate={{ y: 0, opacity: 1, transition: { delay: 1 } }}
      data-role={role}
    >
      <div
        className={cx(
          "flex gap-4 group-data-[role=user]/message:px-3 w-full group-data-[role=user]/message:w-fit group-data-[role=user]/message:ml-auto group-data-[role=user]/message:max-w-2xl group-data-[role=user]/message:py-2 rounded-xl",
          {
            "group-data-[role=user]/message:bg-muted": true,
          },
        )}
      >
        <div className="size-8 flex items-center rounded-full justify-center ring-1 shrink-0 ring-border">
          <SparklesIcon size={14} />
        </div>

        <div className="flex flex-col gap-2 w-full">
          <div className="flex flex-col gap-4 text-muted-foreground">
            Hmm...
          </div>
        </div>
      </div>
    </motion.div>
  );
};
