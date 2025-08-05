"use client";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { AppCard } from "./app-card";
import { useState, useMemo } from "react";
import { App } from "@/lib/types/app";
import { AppCardComingSoon } from "./app-card-coming-soon";
import comingsoon from "@/lib/comingsoon/comingsoon.json";
import { useAppConfigs } from "@/hooks/use-app-config";
import { ArrowUp, ArrowDown } from "lucide-react";

function normalize(str: string): string {
  return str.toLowerCase().replace(/[\s\-_]/g, "");
}

enum ConfigurationFilter {
  ALL = "all",
  CONFIGURED = "configured",
  UNCONFIGURED = "unconfigured",
}

enum AuthType {
  ALL = "All Auth Types",
  API_KEY = "api_key",
  OAUTH2 = "oauth2",
  NO_AUTH = "no_auth",
}

enum SortOption {
  ASC = "asc",
  DESC = "desc",
}

interface AppGridProps {
  apps: App[];
}

export function AppGrid({ apps }: AppGridProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] =
    useState<string>("All Categories");
  const [selectedAuthType, setSelectedAuthType] = useState<string>(
    AuthType.ALL,
  );
  const [sortOrder, setSortOrder] = useState<string>(SortOption.ASC);
  const [configurationFilter, setConfigurationFilter] = useState<string>(
    ConfigurationFilter.ALL,
  );

  const { data: appConfigs = [] } = useAppConfigs();

  const categories = Array.from(new Set(apps.flatMap((app) => app.categories)));

  const authTypes = Array.from(
    new Set(
      apps.flatMap((app) => Object.keys(app.supported_security_schemes || {})),
    ),
  ).filter((authType) =>
    [AuthType.API_KEY, AuthType.OAUTH2, AuthType.NO_AUTH].includes(
      authType as AuthType,
    ),
  );

  const configuredAppNames = useMemo(() => {
    return new Set(appConfigs.map((config) => config.app_name));
  }, [appConfigs]);
  const matchesCategory = useMemo(() => {
    return (app: App, category: string): boolean => {
      switch (category) {
        case "All Categories":
          return true;
        default:
          return app.categories.includes(category);
      }
    };
  }, []);

  const matchesConfigurationStatus = useMemo(() => {
    return (app: App, isConfigured: boolean, filter: string): boolean => {
      switch (filter) {
        case ConfigurationFilter.ALL:
          return true;
        case ConfigurationFilter.CONFIGURED:
          return isConfigured;
        case ConfigurationFilter.UNCONFIGURED:
          return !isConfigured;
        default:
          return true;
      }
    };
  }, []);

  const matchesAuthType = useMemo(() => {
    return (app: App, authType: string): boolean => {
      if (authType === AuthType.ALL) {
        return true;
      }
      return Object.keys(app.supported_security_schemes || {}).includes(
        authType,
      );
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
        case SortOption.ASC:
          return sortedApps.sort((a, b) =>
            a.display_name.localeCompare(b.display_name),
          );
        case SortOption.DESC:
          return sortedApps.sort((a, b) =>
            b.display_name.localeCompare(a.display_name),
          );
        default:
          return sortedApps.sort((a, b) =>
            a.display_name.localeCompare(b.display_name),
          );
      }
    };
  }, []);

  const filteredAndSortedApps = useMemo(() => {
    const filtered = apps.filter((app) => {
      const isConfigured = configuredAppNames.has(app.name);

      return (
        matchesSearchQuery(app, searchQuery) &&
        matchesCategory(app, selectedCategory) &&
        matchesConfigurationStatus(app, isConfigured, configurationFilter) &&
        matchesAuthType(app, selectedAuthType)
      );
    });

    return sortApps(filtered, sortOrder);
  }, [
    apps,
    searchQuery,
    selectedCategory,
    selectedAuthType,
    sortOrder,
    configurationFilter,
    configuredAppNames,
    matchesSearchQuery,
    matchesCategory,
    matchesConfigurationStatus,
    matchesAuthType,
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
      <div className="flex flex-wrap items-center gap-3">
        <Input
          placeholder="Search apps by name, description, or category..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="max-w-sm"
        />

        <Select value={selectedCategory} onValueChange={setSelectedCategory}>
          <SelectTrigger className="w-[170px]">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="All Categories">All Categories</SelectItem>
            {categories.map((category) => (
              <SelectItem key={category} value={category}>
                {category}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select value={selectedAuthType} onValueChange={setSelectedAuthType}>
          <SelectTrigger className="w-[160px]">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value={AuthType.ALL}>All Auth Types</SelectItem>
            {authTypes.map((authType) => (
              <SelectItem key={authType} value={authType}>
                {authType === AuthType.API_KEY && "API Key"}
                {authType === AuthType.OAUTH2 && "OAuth2"}
                {authType === AuthType.NO_AUTH && "No Auth"}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <ToggleGroup
          type="single"
          value={configurationFilter}
          onValueChange={(value) =>
            setConfigurationFilter(value || ConfigurationFilter.ALL)
          }
          className="border rounded-md"
        >
          <ToggleGroupItem
            value={ConfigurationFilter.ALL}
            aria-label="Show all apps"
            className="flex-none px-4"
          >
            All
          </ToggleGroupItem>
          <ToggleGroupItem
            value={ConfigurationFilter.CONFIGURED}
            aria-label="Show configured apps"
            className="flex-none px-4"
          >
            Configured
          </ToggleGroupItem>
          <ToggleGroupItem
            value={ConfigurationFilter.UNCONFIGURED}
            aria-label="Show unconfigured apps"
            className="flex-none px-4"
          >
            Unconfigured
          </ToggleGroupItem>
        </ToggleGroup>

        <ToggleGroup
          type="single"
          value={sortOrder}
          onValueChange={(value) => setSortOrder(value || SortOption.ASC)}
          className="border rounded-md"
        >
          <ToggleGroupItem
            value={SortOption.ASC}
            aria-label="Sort A to Z"
            className="flex-none px-3"
          >
            <ArrowUp className="h-4 w-4" />
            A-Z
          </ToggleGroupItem>
          <ToggleGroupItem
            value={SortOption.DESC}
            aria-label="Sort Z to A"
            className="flex-none px-3"
          >
            <ArrowDown className="h-4 w-4" />
            Z-A
          </ToggleGroupItem>
        </ToggleGroup>

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
        <div className="grow border-t border-border"></div>
        <span className="mx-4 text-4xl font-bold text-foreground">
          Coming Soon
        </span>
        <div className="grow border-t border-border"></div>
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
