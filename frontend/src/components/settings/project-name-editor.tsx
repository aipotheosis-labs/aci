import { useState } from "react";
import { Edit2, Check } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { SettingsItem } from "./settings-item";

interface ProjectNameEditorProps {
  projectName: string;
  onSave: (newName: string) => Promise<void>;
}

export function ProjectNameEditor({
  projectName,
  onSave,
}: ProjectNameEditorProps) {
  const [name, setName] = useState(projectName);
  const [isEditing, setIsEditing] = useState(false);

  const handleSave = async () => {
    if (name.trim() === projectName) {
      setIsEditing(false);
      return;
    }

    setIsEditing(false);
    const newName = name;
    setName(projectName); // Reset to current name immediately

    try {
      await onSave(newName);
    } catch {
      setName(newName); // Restore the new name if save failed
      setIsEditing(true); // Reopen editing if save failed
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      handleSave();
    } else if (e.key === "Escape") {
      setIsEditing(false);
      setName(projectName);
    }
  };

  return (
    <SettingsItem
      icon={Edit2}
      label="Project Name"
      description={
        <div className="flex items-center gap-2 mt-1">
          {isEditing ? (
            <>
              <Input
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-96"
                onKeyDown={handleKeyDown}
                autoFocus
              />
              <Button
                size="sm"
                variant="ghost"
                onClick={handleSave}
                className="h-8 w-8 p-0"
              >
                <Check className="h-4 w-4" />
              </Button>
            </>
          ) : (
            <>
              <span className="text-sm text-muted-foreground">
                {projectName}
              </span>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    onClick={() => setIsEditing(true)}
                    className="h-8 w-8 p-0"
                  >
                    <Edit2 className="h-4 w-4" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>
                  <p>Click to edit project name</p>
                </TooltipContent>
              </Tooltip>
            </>
          )}
        </div>
      }
    />
  );
}
