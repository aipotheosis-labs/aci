import { cn } from "@/lib/utils";
import { Progress } from "@/components/ui/progress";
import { FaCheck } from "react-icons/fa6";

interface StepperProps {
  currentStep: number;
  totalSteps: number;
  steps: { id: number; title: string }[];
}

export function Stepper({ currentStep, totalSteps, steps }: StepperProps) {
  return (
    <div className="py-1">
      <div className="flex justify-between items-center relative">
        {steps.map((step) => (
          <div key={step.id} className="flex flex-col items-center z-10">
            <div
              className={cn(
                "w-8 h-8 rounded-full flex items-center justify-center text-xs mb-1 transition-colors",
                currentStep === step.id
                  ? "bg-primary text-primary-foreground"
                  : currentStep > step.id
                    ? "bg-[#1CD1AF] text-white"
                    : "bg-muted text-muted-foreground",
              )}
            >
              {currentStep > step.id ? (
                <FaCheck className="text-white" />
              ) : (
                step.id
              )}
            </div>
            <span className="text-xs font-medium text-muted-foreground">
              {step.title}
            </span>
          </div>
        ))}

        <div className="absolute left-[calc(5%)] right-[calc(7%)] top-[16px] h-[2px] bg-muted -z-0">
          <Progress
            className="h-[2px]"
            value={((currentStep - 1) / (totalSteps - 1)) * 100}
          />
        </div>
      </div>
    </div>
  );
}
