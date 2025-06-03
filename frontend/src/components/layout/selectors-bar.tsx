"use client";

import { OrgSelector } from "./org-selector";
import { ProjectSelector } from "./project-selector";

export const SelectorsBar = () => {
  return (
    <div className="sticky top-0 z-50 bg-sidebar border-b border-sidebar-border pt-4 pb-4">
      <div className="w-fit px-4">
        <div className="flex items-center gap-2">
          <OrgSelector />
          <ProjectSelector />
        </div>
      </div>
    </div>
  );
};
