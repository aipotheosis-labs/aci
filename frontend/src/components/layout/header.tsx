"use client";

// import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogTrigger,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
// import { GoBell } from "react-icons/go";
import { BsQuestionCircle, BsGithub, BsBook, BsDiscord } from "react-icons/bs";
import { Separator } from "@/components/ui/separator";
import { BreadcrumbLinks } from "./BreadcrumbLinks";
import { usePathname } from "next/navigation";
import { ProjectSelector } from "./project-selector";
import { OrgSelector } from "./org-selector";

export const Header = () => {
  const pathname = usePathname();

  return (
    <div>
      <div className="flex w-full items-center justify-between px-4 py-3">
        <div className="flex items-center gap-4">
          {/* Organization, Project Selectors and Breadcrumbs */}
          <div className="flex items-center gap-2">
            <div className="w-44">
              <OrgSelector />
            </div>
            <span className="text-gray-400">/</span>
            <div className="w-44">
              <ProjectSelector />
            </div>
            <span className="text-gray-400">/</span>
            <BreadcrumbLinks pathname={pathname} />
          </div>
        </div>

        {/* <Input
          placeholder="Search keyword, category, etc."
          className="mx-2 w-80"
        /> */}

        <div className="flex items-center gap-2">
          <a
            href="https://discord.gg/bT2eQ2m9vm"
            target="_blank"
            rel="noopener noreferrer"
          >
            <Button variant="outline" className="px-2 h-9">
              <BsDiscord />
              <span>Discord</span>
            </Button>
          </a>

          <a
            href="https://github.com/aipotheosis-labs/aci"
            target="_blank"
            rel="noopener noreferrer"
          >
            <Button variant="outline" className="px-2 h-9">
              <BsGithub />
              <span>GitHub</span>
            </Button>
          </a>

          <a
            href="https://aci.dev/docs"
            target="_blank"
            rel="noopener noreferrer"
          >
            <Button variant="outline" className="px-2 h-9">
              <BsBook />
              <span>Docs</span>
            </Button>
          </a>

          {/* <Button variant="outline" className="px-2 mx-2">
            <GoBell />
          </Button> */}
          <Dialog>
            <DialogTrigger asChild>
              <Button variant="outline" className="px-2 h-9">
                <BsQuestionCircle />
                <span>Support</span>
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Support</DialogTitle>
              </DialogHeader>
              <p>
                For support or to report a bug, please email us at
                support@aipolabs.xyz
              </p>
            </DialogContent>
          </Dialog>
        </div>
      </div>
      <Separator />
    </div>
  );
};
