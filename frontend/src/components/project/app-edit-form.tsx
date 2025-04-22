"use client";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Checkbox } from "@/components/ui/checkbox";
import { useState, useEffect } from "react";
import { Input } from "@/components/ui/input";
import { IoMdClose } from "react-icons/io";
import { IoSearchOutline } from "react-icons/io5";
import { Separator } from "@/components/ui/separator";
import { getAllAppConfigs } from "@/lib/api/appconfig";
import { updateAgent } from "@/lib/api/agent";
import { AppConfig } from "@/lib/types/appconfig";
import { getApiKey } from "@/lib/api/util";
import { toast } from "sonner";
import { useMetaInfo } from "@/components/context/metainfo";
import { IdDisplay } from "../apps/id-display";
interface AppEditFormProps {
  children: React.ReactNode;
  reload: () => Promise<void>;
  initialSelectedApps?: string[];
  projectId: string;
  agentId: string;
  allowedApps: string[];
}

export function AppEditForm({
  children,
  reload,
  initialSelectedApps = [],
  projectId,
  agentId,
  allowedApps,
}: AppEditFormProps) {
  const { accessToken } = useMetaInfo();
  const [open, setOpen] = useState(false);
  const [selectedApps, setSelectedApps] = useState<string[]>(
    allowedApps || initialSelectedApps,
  );
  const [searchTerm, setSearchTerm] = useState("");
  const [appConfigs, setAppConfigs] = useState<AppConfig[]>([]);
  const [loading, setLoading] = useState(false);
  const { activeProject } = useMetaInfo();

  useEffect(() => {
    if (!open) return;

    const apiKey = getApiKey(activeProject);
    const fetchAppConfigs = async () => {
      try {
        setLoading(true);
        const configs = await getAllAppConfigs(apiKey);
        console.log("configs", configs);

        setAppConfigs(configs);
        setLoading(false);
      } catch (error) {
        console.error("Failed to fetch app configurations:", error);
        setLoading(false);
      }
    };

    fetchAppConfigs();
  }, [activeProject, open]);

  useEffect(() => {
    if (allowedApps) {
      setSelectedApps(allowedApps);
    }
  }, [allowedApps]);

  const appNames = appConfigs.map((config) => config.app_name);
  const filteredApps = appNames.filter((app) =>
    app.toLowerCase().includes(searchTerm.toLowerCase()),
  );

  const handleSubmit = async () => {
    try {
      if (projectId && agentId) {
        await updateAgent(
          projectId,
          agentId,
          accessToken,
          undefined,
          undefined,
          selectedApps,
        );

        toast.success("Agent's allowed apps have been updated successfully.");

        reload();
      }
      setOpen(false);
    } catch (error) {
      console.error("Failed to update agent's allowed apps:", error);
      toast.error("Failed to update agent's allowed apps.");
    }
  };

  const handleClose = () => {
    setOpen(false);
    setSearchTerm("");
    setSelectedApps(allowedApps || initialSelectedApps);
  };

  const toggleApp = (app: string) => {
    if (selectedApps.includes(app)) {
      setSelectedApps(selectedApps.filter((a) => a !== app));
    } else {
      setSelectedApps([...selectedApps, app]);
    }
  };

  const selectAll = () => {
    setSelectedApps([...appNames]);
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>{children}</DialogTrigger>
      <DialogContent className="sm:max-w-[425px] ">
        <DialogHeader className="space-y-4">
          <div className="flex items-center justify-between">
            <DialogTitle>Edit Allowed Apps</DialogTitle>
          </div>
          <p className="text-sm text-gray-500 mt-2">
            Select what apps are enabled for this agent.
          </p>
          <Separator />
          <h3 className="text-sm font-medium">
            Select Apps to Enable
            {selectedApps.length > 0 && (
              <div className="max-w-[300px] truncate">
                <IdDisplay id={selectedApps.join(",")} />
              </div>
            )}
          </h3>

          {selectedApps.length > 0 && (
            <div className="flex flex-wrap gap-2 p-2 rounded-md overflow-y-auto max-h-16 border">
              {selectedApps.map((app) => (
                <div
                  key={app}
                  className="flex items-center gap-1 px-2 py-1 max-h-9 bg-gray-100 rounded-md"
                >
                  {app}
                  <button
                    onClick={() => toggleApp(app)}
                    className="text-gray-500 hover:text-gray-700"
                  >
                    <IoMdClose size={14} />
                  </button>
                </div>
              ))}
            </div>
          )}
        </DialogHeader>

        <div className="space-y-4">
          <div className="border rounded-md p-4">
            <div className="flex items-center gap-2 px-3 py-2 bg-white border rounded-md mb-3">
              <IoSearchOutline className="text-gray-400" size={20} />
              <Input
                type="text"
                placeholder="Search App"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="border-0 shadow-none p-0 focus-visible:ring-0 placeholder:text-gray-400"
              />
            </div>

            {loading ? (
              <div className="flex h-40  justify-center py-4 ">
                <p>Loading...</p>
              </div>
            ) : appConfigs.length === 0 ? (
              <div className="flex h-40  justify-center py-4">
                <p>No app configurations available</p>
              </div>
            ) : (
              <div className="space-y-1 h-40 overflow-y-auto ">
                {filteredApps.map((app) => (
                  <div
                    key={app}
                    className={`flex items-center p-2 rounded-md cursor-pointer ${
                      selectedApps.includes(app)
                        ? "border-[#1CD1AF] border bg-[#EFFFFC]"
                        : " hover:bg-gray-50"
                    }`}
                    onClick={() => toggleApp(app)}
                  >
                    <Checkbox
                      id={`list-${app}`}
                      checked={selectedApps.includes(app)}
                      className={
                        selectedApps.includes(app)
                          ? "border-[#1CD1AF] bg-[#1CD1AF] text-white"
                          : "border-gray-300"
                      }
                    />
                    <label
                      htmlFor={`list-${app}`}
                      className="ml-3 text-sm font-medium cursor-pointer flex-1"
                    >
                      {app}
                    </label>
                  </div>
                ))}
              </div>
            )}

            <div className="flex justify-between mt-4">
              <Button
                variant="ghost"
                onClick={() => setSelectedApps([])}
                className="text-gray-500 hover:bg-transparent hover:text-gray-700"
              >
                Clear Selection
              </Button>
              <Button
                variant="ghost"
                onClick={selectAll}
                className="text-[#1CD1AF] hover:bg-transparent hover:text-[#19bd9e]"
              >
                Select All
              </Button>
            </div>
          </div>

          <Separator />

          <div className="flex justify-end gap-2">
            <Button
              variant="outline"
              onClick={handleClose}
              className="text-gray-500"
            >
              Cancel
            </Button>
            <Button
              onClick={handleSubmit}
              className="bg-[#1CD1AF] hover:bg-[#19bd9e] text-white"
            >
              Save
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
