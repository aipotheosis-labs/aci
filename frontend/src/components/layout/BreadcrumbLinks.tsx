"use client";

import Link from "next/link";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";
import { sidebarItems, settingsItems } from "./app-sidebar";

interface BreadcrumbLinksProps {
  pathname: string;
}

export const BreadcrumbLinks = ({ pathname }: BreadcrumbLinksProps) => {
  const segments = pathname.split("/").filter(Boolean);
  let cumulativePath = "";
  const allRoutes = [...sidebarItems, ...settingsItems];
  const breadcrumbs = segments.map((segment, index) => {
    cumulativePath += "/" + segment;

    if (index === 0) {
      const matchingRoute = allRoutes.find(
        (item) =>
          item.url === cumulativePath || item.url.startsWith(cumulativePath),
      );

      if (matchingRoute) {
        return { label: matchingRoute.title, href: cumulativePath };
      }
    }

    return { label: segment.toUpperCase(), href: cumulativePath };
  });

  const breadcrumbsList = [];

  for (let i = 0; i < breadcrumbs.length; i++) {
    if (i > 0) {
      breadcrumbsList.push(<BreadcrumbSeparator key={i * 2 - 1} />);
    }

    breadcrumbsList.push(
      <BreadcrumbItem key={i * 2}>
        <Link href={breadcrumbs[i].href}>{breadcrumbs[i].label}</Link>
      </BreadcrumbItem>,
    );
  }

  return (
    <Breadcrumb>
      <BreadcrumbList>
        {breadcrumbs.length > 0 ? (
          breadcrumbsList
        ) : (
          <BreadcrumbItem>
            <BreadcrumbLink href="/">Home</BreadcrumbLink>
          </BreadcrumbItem>
        )}
      </BreadcrumbList>
    </Breadcrumb>
  );
};
