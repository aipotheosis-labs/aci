import { Alert, AlertDescription } from "@/components/ui/alert";
import { X } from "lucide-react";
import { useState } from "react";
import { cn } from "@/lib/utils";

export const BetaAlert = () => {
  const [visible, setVisible] = useState(true);
  if (!visible) return null;

  return (
    <Alert
      variant="default"
      className={cn(
        "relative m-1 w-[calc(100%-0.5rem)] pr-10",
        "bg-blue-100 text-blue-800 border border-blue-200",
      )}
    >
      <AlertDescription>
        Agent Playground is a beta feature and not recommended for production
        use. Expect limited stability and possible changes.
      </AlertDescription>

      <button
        className="absolute top-2 right-2 text-blue-800 hover:text-blue-600"
        onClick={() => setVisible(false)}
        aria-label="Close beta alert"
      >
        <X className="w-4 h-4" />
      </button>
    </Alert>
  );
};
