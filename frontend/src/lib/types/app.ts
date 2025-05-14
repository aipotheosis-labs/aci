import { AppFunction } from "./appfunction";

export interface App {
  id: string;
  name: string;
  display_name: string;
  provider: string;
  version: string;
  description: string;
  logo: string;
  categories: string[];
  visibility: string;
  active: boolean;
  functions: AppFunction[];
  supported_security_schemes: Record<string, { scope?: string }>;
  created_at: string;
  updated_at: string;
}
