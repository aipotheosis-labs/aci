import { ReactNode } from "react";
import { cn } from "@/lib/utils";

interface StatsContainerProps {
  children: ReactNode;
  className?: string;
}

export function StatsContainer({ children, className }: StatsContainerProps) {
  return (
    <div className={cn("rounded-xl border bg-card", className)}>
      <div className="grid sm:grid-cols-2 lg:grid-cols-4">
        {Array.isArray(children)
          ? children.map((child, index) => (
              <div
                key={index}
                className={cn(
                  "relative",
                  index !== 0 &&
                    "before:absolute before:inset-y-4 before:left-0 before:w-px before:bg-border",
                )}
              >
                {child}
              </div>
            ))
          : children}
      </div>
    </div>
  );
}
