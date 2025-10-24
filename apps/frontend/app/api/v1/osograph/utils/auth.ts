import { createAdminClient } from "@/lib/supabase/admin";
import type { OrgUser } from "@/lib/types/user";
import {
  AuthenticationErrors,
  UserErrors,
  OrganizationErrors,
} from "&/utils/errors";

export type AuthenticatedUser = Extract<OrgUser, { role: "user" }>;

export type GraphQLContext = {
  req: Request;
  user: OrgUser;
};

export function isAuthenticated(user: OrgUser): user is AuthenticatedUser {
  return user.role !== "anonymous";
}

export function requireAuthentication(user: OrgUser): AuthenticatedUser {
  if (!isAuthenticated(user)) {
    throw AuthenticationErrors.notAuthenticated();
  }
  return user;
}

export async function requireOrgMembership(
  userId: string,
  orgId: string,
): Promise<void> {
  const supabase = createAdminClient();

  const { data: membership } = await supabase
    .from("users_by_organization")
    .select("id")
    .eq("user_id", userId)
    .eq("org_id", orgId)
    .is("deleted_at", null)
    .single();

  if (!membership) {
    throw AuthenticationErrors.notAuthorized();
  }
}

export async function getUserProfile(userId: string) {
  const supabase = createAdminClient();

  const { data: profile, error } = await supabase
    .from("user_profiles")
    .select("*")
    .eq("id", userId)
    .single();

  if (error || !profile) {
    throw UserErrors.profileNotFound();
  }

  return profile;
}

export async function getOrganization(orgId: string) {
  const supabase = createAdminClient();

  const { data: org, error } = await supabase
    .from("organizations")
    .select("*")
    .eq("id", orgId)
    .single();

  if (error || !org) {
    throw OrganizationErrors.notFound();
  }

  return org;
}

export async function getOrganizationByName(orgName: string) {
  const supabase = createAdminClient();

  const { data: org, error } = await supabase
    .from("organizations")
    .select("*")
    .eq("org_name", orgName)
    .single();

  if (error || !org) {
    throw OrganizationErrors.notFound();
  }

  return org;
}
