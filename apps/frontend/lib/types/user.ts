export type UserRole = "anonymous" | "user" | "admin";
export type OrgRole = "admin" | "member";

interface BaseUser {
  role: UserRole;
  host: string | null;
}

export type AnonUser = BaseUser & {
  role: "anonymous";
};

export interface UserDetails {
  userId: string;
  keyName: string;
  email?: string;
  name: string;
}

export interface OrganizationDetails {
  orgId: string;
  orgName: string;
  orgRole: OrgRole;
}

export type NormalUser = BaseUser &
  UserDetails &
  Partial<OrganizationDetails> & {
    role: "user";
  };

export type AdminUser = BaseUser &
  UserDetails &
  Partial<OrganizationDetails> & {
    role: "admin";
  };

export type AuthUser = NormalUser | AdminUser;
export type User = AnonUser | AuthUser;
