import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "sonner";
import { ArrowUp, StopCircle } from "lucide-react";
import { useCallback, memo } from "react";
import { UseChatHelpers } from "ai/react";

interface ChatInputProps {
  input: string;
  handleInputChange: (e: React.ChangeEvent<HTMLTextAreaElement>) => void;
  handleSubmit: (e: React.FormEvent<HTMLFormElement>) => void;
  status: string;
  linkedAccountOwnerId: string | null;
  stop?: () => void;
  setMessages?: UseChatHelpers["setMessages"];
}

function PureStopButton({
  stop,
  setMessages,
}: {
  stop: () => void;
  setMessages: UseChatHelpers["setMessages"];
}) {
  return (
    <Button
      type="button"
      data-testid="stop-button"
      className="rounded-full p-1.5 h-fit border dark:border-zinc-600"
      onClick={(event) => {
        event.preventDefault();
        stop();
        setMessages((messages) => messages);
      }}
    >
      <StopCircle size={14} />
    </Button>
  );
}

const StopButton = memo(PureStopButton);

function PureSendButton({ input }: { input: string }) {
  return (
    <Button
      data-testid="send-button"
      className="rounded-full p-1.5 h-fit border dark:border-zinc-600"
      disabled={input.length === 0}
    >
      <ArrowUp size={14} />
    </Button>
  );
}

const SendButton = memo(PureSendButton, (prevProps, nextProps) => {
  if ((prevProps.input.length === 0) !== (nextProps.input.length === 0))
    return false;
  return true;
});

export function ChatInput({
  input,
  handleInputChange,
  handleSubmit,
  status,
  linkedAccountOwnerId,
  stop,
  setMessages,
}: ChatInputProps) {
  const submitForm = useCallback(
    (e?: React.FormEvent<HTMLFormElement>) => {
      e?.preventDefault();
      handleSubmit(e as React.FormEvent<HTMLFormElement>);
    },
    [handleSubmit],
  );

  return (
    <div className="pt-4 border-none relative -mt-6 z-10">
      <form
        onSubmit={submitForm}
        className="flex flex-col w-full max-w-3xl mx-auto"
      >
        <div className="flex flex-col items-start bg-white rounded-2xl border shadow-sm">
          <div className="relative w-full">
            <Textarea
              value={input}
              placeholder="Ask me anything..."
              onChange={handleInputChange}
              onKeyDown={(event) => {
                if (!linkedAccountOwnerId) {
                  toast.error("Please select a linked account owner");
                  return;
                }
                if (
                  event.key === "Enter" &&
                  !event.shiftKey &&
                  linkedAccountOwnerId
                ) {
                  event.preventDefault();
                  if (status === "submitted" || status === "streaming") {
                    toast.error(
                      "Please wait for the previous request to complete",
                    );
                    return;
                  } else {
                    submitForm();
                  }
                }
              }}
              className="flex-1 p-4 pr-20 bg-transparent outline-none resize-none min-h-[4rem] border-none shadow-none focus-visible:ring-0 focus-visible:ring-offset-0 focus-visible:outline-none"
              disabled={status !== "ready"}
              rows={2}
            />
            <div className="pointer-events-none">
              <div className="absolute top-1/2 right-4 -translate-y-1/2 flex flex-row justify-end pointer-events-auto">
                {status === "submitted" || status === "streaming" ? (
                  <StopButton stop={stop!} setMessages={setMessages!} />
                ) : (
                  <SendButton input={input} />
                )}
              </div>
            </div>
          </div>
        </div>
      </form>
    </div>
  );
}
