"use client";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { AppCard } from "./app-card";
import { useState, useMemo } from "react";
import { App } from "@/lib/types/app";
import { AppCardComingSoon } from "./app-card-coming-soon";
import comingsoon from "@/lib/comingsoon/comingsoon.json";
import { useAppConfigs } from "@/hooks/use-app-config";

function normalize(str: string): string {
  return str.toLowerCase().replace(/[\s\-_]/g, "");
}
enum FilterCategory {
  ALL = "all",
  CONFIGURED = "configured",
  UNCONFIGURED = "unconfigured",
}

enum SortOption {
  DEFAULT = "default",
  ALPHABETICAL = "alphabetical",
  REVERSE_ALPHABETICAL = "reverse-alphabetical",
}

interface AppGridProps {
  apps: App[];
}

export function AppGrid({ apps }: AppGridProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<string>(
    FilterCategory.ALL,
  );
  const [sortOrder, setSortOrder] = useState<string>(SortOption.DEFAULT);

  const { data: appConfigs = [] } = useAppConfigs();

  const categories = Array.from(new Set(apps.flatMap((app) => app.categories)));

  const configuredAppNames = useMemo(() => {
    return new Set(appConfigs.map((config) => config.app_name));
  }, [appConfigs]);
  const matchesCategory = useMemo(() => {
    return (app: App, category: string, isConfigured: boolean): boolean => {
      switch (category) {
        case FilterCategory.ALL:
          return true;
        case FilterCategory.CONFIGURED:
          return isConfigured;
        case FilterCategory.UNCONFIGURED:
          return !isConfigured;
        default:
          return app.categories.includes(category);
      }
    };
  }, []);

  const matchesSearchQuery = useMemo(() => {
    return (app: App, query: string): boolean => {
      if (!query) return true;

      const lowerQuery = query.toLowerCase();
      return (
        app.name.toLowerCase().includes(lowerQuery) ||
        app.description.toLowerCase().includes(lowerQuery) ||
        app.categories.some((c) => c.toLowerCase().includes(lowerQuery))
      );
    };
  }, []);

  const sortApps = useMemo(() => {
    return (apps: App[], sortOption: string): App[] => {
      const sortedApps = [...apps];

      switch (sortOption) {
        case SortOption.ALPHABETICAL:
          return sortedApps.sort((a, b) =>
            a.display_name.localeCompare(b.display_name),
          );
        case SortOption.REVERSE_ALPHABETICAL:
          return sortedApps.sort((a, b) =>
            b.display_name.localeCompare(a.display_name),
          );
        case SortOption.DEFAULT:
        default:
          return sortedApps;
      }
    };
  }, []);

  const filteredAndSortedApps = useMemo(() => {
    const filtered = apps.filter((app) => {
      const isConfigured = configuredAppNames.has(app.name);

      return (
        matchesSearchQuery(app, searchQuery) &&
        matchesCategory(app, selectedCategory, isConfigured)
      );
    });

    return sortApps(filtered, sortOrder);
  }, [
    apps,
    searchQuery,
    selectedCategory,
    sortOrder,
    configuredAppNames,
    matchesSearchQuery,
    matchesCategory,
    sortApps,
  ]);

  const liveAppKeys = useMemo(() => {
    const keys = new Set<string>();
    apps.forEach((app) => {
      keys.add(normalize(app.name));
      // Since the names are not uniform, use a filter to make unique
      if (app.display_name && app.display_name !== app.name) {
        keys.add(normalize(app.display_name));
      }
    });
    return keys;
  }, [apps]);

  const comingSoonApps = useMemo(() => {
    return comingsoon.filter((app) => !liveAppKeys.has(normalize(app.title)));
  }, [liveAppKeys]);

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Input
          placeholder="Search apps by name, description, or category..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="max-w-sm"
        />

        <Select onValueChange={setSelectedCategory}>
          <SelectTrigger className="w-[160px]">
            <SelectValue placeholder="all" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value={FilterCategory.ALL}>All Apps</SelectItem>
            <SelectItem value={FilterCategory.CONFIGURED}>
              Configured Apps
            </SelectItem>
            <SelectItem value={FilterCategory.UNCONFIGURED}>
              Unconfigured Apps
            </SelectItem>
            {categories.map((category) => (
              <SelectItem key={category} value={category}>
                {category}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select onValueChange={setSortOrder}>
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Default" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value={SortOption.DEFAULT}>Default</SelectItem>
            <SelectItem value={SortOption.ALPHABETICAL}>
              Ascending A-Z
            </SelectItem>
            <SelectItem value={SortOption.REVERSE_ALPHABETICAL}>
              Descending Z-A
            </SelectItem>
          </SelectContent>
        </Select>

        {/* <Select onValueChange={setSelectedTag}>
          <SelectTrigger className="w-[80px]">
            <SelectValue placeholder="Tags" />
          </SelectTrigger>
          <SelectContent>
            {["all", ...tags].map((tag) => (
              <SelectItem key={tag} value={tag}>
                {tag}
              </SelectItem>
            ))}
          </SelectContent>
        </Select> */}
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {filteredAndSortedApps.map((app) => (
          <AppCard
            key={app.id}
            app={app}
            isConfigured={configuredAppNames.has(app.name)}
          />
        ))}
      </div>

      <div className="relative flex items-center my-6">
        <div className="grow border-t border-gray-300"></div>
        <span className="mx-4 text-4xl font-bold text-gray-700">
          Coming Soon
        </span>
        <div className="grow border-t border-gray-300"></div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {comingSoonApps.map((app) => {
          return (
            <AppCardComingSoon
              key={app.title}
              title={app.title}
              description={app.description}
              logo={app.logo}
            />
          );
        })}
      </div>

      {filteredAndSortedApps.length === 0 && (
        <div className="text-center text-muted-foreground">
          No apps found matching your criteria
        </div>
      )}
    </div>
  );
}
