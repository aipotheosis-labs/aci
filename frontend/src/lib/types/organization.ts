export enum OrganizationRole {
  Owner = "Owner",
  Admin = "Admin",
}

export interface OrganizationUser {
  user_id: string;
  email: string;
  role: OrganizationRole;
  first_name?: string;
  last_name?: string;
}

export interface OrganizationMemberUpdate {
  role: OrganizationRole;
}
