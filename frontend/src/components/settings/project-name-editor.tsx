import { useState } from "react";
import { Edit2, Check } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
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
    await onSave(name);
    setIsEditing(false);
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
        <div className="flex items-center gap-2">
          <Input
            value={name}
            onChange={(e) => setName(e.target.value)}
            onFocus={() => setIsEditing(true)}
            onBlur={handleSave}
            onKeyDown={handleKeyDown}
            className="w-96"
            placeholder="Enter project name"
          />
          {isEditing && (
            <Button
              size="sm"
              variant="ghost"
              onClick={handleSave}
              className="h-8 w-8 p-0"
            >
              <Check className="h-4 w-4" />
            </Button>
          )}
        </div>
      }
    />
  );
}
