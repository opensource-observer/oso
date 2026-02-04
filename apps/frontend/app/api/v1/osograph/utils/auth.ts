import type { AuthenticatedUser } from "@/app/api/v1/osograph/types/context";
import {
  AuthenticationErrors,
  OrganizationErrors,
  UserErrors,
} from "@/app/api/v1/osograph/utils/errors";
import {
  createAdminClient,
  type SupabaseAdminClient,
} from "@/lib/supabase/admin";
import {
  organizationsRowSchema,
  userProfilesRowSchema,
} from "@/lib/types/schema";
import type { User } from "@/lib/types/user";
import { z } from "zod";

export function isAuthenticated(user: User): user is AuthenticatedUser {
  return user.role !== "anonymous";
}

export function requireAuthentication(user: User): AuthenticatedUser {
  if (!isAuthenticated(user)) {
    throw AuthenticationErrors.notAuthenticated();
  }
  return user;
}

export async function requireOrgMembership(
  userId: string,
  orgId: string,
  adminClient: SupabaseAdminClient,
): Promise<void>;
/** @deprecated */
export async function requireOrgMembership(
  userId: string,
  orgId: string,
): Promise<void>;
export async function requireOrgMembership(
  userId: string,
  orgId: string,
  adminClient?: SupabaseAdminClient,
): Promise<void> {
  const supabase = adminClient ?? createAdminClient();

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

export async function getUserProfile(
  userId: string,
  adminClient: SupabaseAdminClient,
): Promise<z.infer<typeof userProfilesRowSchema>>;
/** @deprecated */
export async function getUserProfile(
  userId: string,
): Promise<z.infer<typeof userProfilesRowSchema>>;
export async function getUserProfile(
  userId: string,
  adminClient?: SupabaseAdminClient,
) {
  const supabase = adminClient ?? createAdminClient();

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

export async function getOrganization(
  orgId: string,
  adminClient: SupabaseAdminClient,
): Promise<z.infer<typeof organizationsRowSchema>>;
/** @deprecated */
export async function getOrganization(
  orgId: string,
): Promise<z.infer<typeof organizationsRowSchema>>;
export async function getOrganization(
  orgId: string,
  adminClient?: SupabaseAdminClient,
) {
  const supabase = adminClient ?? createAdminClient();

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
