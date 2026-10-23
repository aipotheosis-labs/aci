"use client";

import * as React from "react";
import { Switch as ShadcnSwitch } from "@/components/ui/switch";
import { toast } from "sonner";
import { cn } from "@/lib/utils";

interface EnhancedSwitchProps extends React.ComponentPropsWithoutRef<
  typeof ShadcnSwitch
> {
  /** Async function to call when the switch toggles, should return a boolean indicating if the operation was successful */
  onAsyncChange?: (checked: boolean) => Promise<boolean>;
  /**
   * Message or a function to generate one based on the new state.
   */
  successMessage?: string | ((newState: boolean) => string);
  errorMessage?: string | ((newState: boolean) => string);
  /** Custom class name for the active state background color */
  activeClassName?: string;
}

export const EnhancedSwitch = React.forwardRef<
  React.ComponentRef<typeof ShadcnSwitch>,
  EnhancedSwitchProps
>(
  (
    {
      checked,
      onCheckedChange,
      onAsyncChange,
      disabled,
      successMessage = "Update successful",
      errorMessage = "Update failed",
      className,
      activeClassName = "bg-[#1CD1AF]",
      ...props
    },
    ref,
  ) => {
    const [internalChecked, setInternalChecked] = React.useState(
      checked || false,
    );
    const [isLoading, setIsLoading] = React.useState(false);

    // Synchronize external checked state
    React.useEffect(() => {
      if (checked !== undefined) {
        setInternalChecked(checked);
      }
    }, [checked]);

    const getMessageContent = (
      message: string | ((newState: boolean) => string),
      state: boolean,
    ) => {
      return typeof message === "function" ? message(state) : message;
    };

    const handleChange = async (newState: boolean) => {
      // Update internal state optimistically
      setInternalChecked(newState);

      // Call external onChange handler if available
      if (onCheckedChange) {
        onCheckedChange(newState);
      }

      // If no asynchronous handler is provided, return immediately
      if (!onAsyncChange) return;

      try {
        setIsLoading(true);
        const success = await onAsyncChange(newState);

        if (success) {
          // Operation succeeded, keep the new state
          // Display a success message, using either a static string or a function based on the new state
          toast.success(getMessageContent(successMessage, newState));
        } else {
          setInternalChecked(!newState);
          toast.error(getMessageContent(errorMessage, !newState));
        }
      } catch (error) {
        // Error occurred, revert the state
        setInternalChecked(!newState);
        console.error("Switch toggle failed:", error);
        toast.error(getMessageContent(errorMessage, !newState));
      } finally {
        setIsLoading(false);
      }
    };

    return (
      <ShadcnSwitch
        ref={ref}
        checked={internalChecked}
        onCheckedChange={handleChange}
        disabled={disabled || isLoading}
        className={cn(
          internalChecked ? activeClassName : "",
          isLoading && "opacity-70 cursor-wait",
          className,
        )}
        {...props}
      />
    );
  },
);

EnhancedSwitch.displayName = "EnhancedSwitch";
