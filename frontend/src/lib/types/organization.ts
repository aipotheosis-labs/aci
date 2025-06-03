export enum OrganizationRole {
  Owner = "Owner",
  Admin = "Admin",
  Member = "Member",
}

export interface OrganizationMember {
  user_id: string;
  email: string;
  role: OrganizationRole;
  first_name?: string;
  last_name?: string;
}

export interface OrganizationMemberUpdate {
  role: OrganizationRole;
}
