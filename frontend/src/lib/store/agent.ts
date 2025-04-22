import { create } from "zustand";
import { getApiKey } from "../api/util";
import { Project } from "../types/project";
interface AgentState {
  selectedApps: string[];
  linkedAccountOwnerId: string;
  allowedApps: string[];
  selectedFunctions: string[];
  selectedAgent: string;
  setSelectedApps: (apps: string[]) => void;
  setLinkedAccountOwnerId: (id: string) => void;
  setAllowedApps: (apps: string[]) => void;
  setSelectedFunctions: (functions: string[]) => void;
  setSelectedAgent: (id: string) => void;
  getApiKey: (activeProject: Project) => string;
}

export const useAgentStore = create<AgentState>()((set, get) => ({
  selectedApps: [],
  linkedAccountOwnerId: "",
  allowedApps: [],
  selectedFunctions: [],
  selectedAgent: "",
  setSelectedApps: (apps: string[]) =>
    set((state) => ({ ...state, selectedApps: apps })),
  setLinkedAccountOwnerId: (id: string) =>
    set((state) => ({ ...state, linkedAccountOwnerId: id })),
  setAllowedApps: (apps: string[]) =>
    set((state) => ({ ...state, allowedApps: apps })),
  setSelectedFunctions: (functions: string[]) =>
    set((state) => ({ ...state, selectedFunctions: functions })),
  setSelectedAgent: (id: string) =>
    set((state) => ({ ...state, selectedAgent: id })),
  getApiKey: (activeProject: Project) => {
    const apiKey = getApiKey(activeProject, get().selectedAgent);
    return apiKey;
  },
}));
