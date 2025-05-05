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
  security_schemes: string[];
  functions: AppFunction[];
  created_at: string;
  updated_at: string;
}
