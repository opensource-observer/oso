import { createAdminClient } from "@/lib/supabase/admin";
import {
  buildConnection,
  emptyConnection,
  type Connection,
} from "@/app/api/v1/osograph/utils/connection";
import type { ConnectionArgs } from "@/app/api/v1/osograph/utils/pagination";
import {
  getFetchLimit,
  getPaginationParams,
} from "@/app/api/v1/osograph/utils/pagination";
import {
  getOrganization,
  requireOrgMembership,
} from "@/app/api/v1/osograph/utils/auth";
import { Database } from "@/lib/types/supabase";

export function preparePaginationRange(args: ConnectionArgs): [number, number] {
  const limit = getFetchLimit(args);
  const { offset } = getPaginationParams(args);
  return [offset, offset + limit - 1];
}

export function buildConnectionOrEmpty<T>(
  data: T[] | null | undefined,
  args: ConnectionArgs,
  count: number | null,
): Connection<T> {
  if (!data || data.length === 0) {
    return emptyConnection();
  }
  return buildConnection(data, args, count ?? 0);
}

export async function getUserOrganizationIds(
  userId: string,
): Promise<string[]> {
  const supabase = createAdminClient();

  const { data: memberships } = await supabase
    .from("users_by_organization")
    .select("org_id")
    .eq("user_id", userId)
    .is("deleted_at", null);

  return memberships?.map((m) => m.org_id) || [];
}

export async function getUserOrganizationsConnection(
  userId: string,
  args: ConnectionArgs,
): Promise<Connection<any>> {
  const supabase = createAdminClient();
  const [start, end] = preparePaginationRange(args);

  const { data: memberships, count } = await supabase
    .from("users_by_organization")
    .select("org_id, organizations(*)", { count: "exact" })
    .eq("user_id", userId)
    .is("deleted_at", null)
    .range(start, end);

  if (!memberships || memberships.length === 0) {
    return emptyConnection();
  }

  const organizations = memberships
    .map((m) => m.organizations)
    .filter((org) => org !== null);

  return buildConnectionOrEmpty(organizations, args, count);
}

export async function getUserInvitationsConnection(
  email: string | null | undefined,
  args: ConnectionArgs,
): Promise<Connection<any>> {
  if (!email) {
    return emptyConnection();
  }

  const supabase = createAdminClient();
  const userEmail = email.toLowerCase();
  const [start, end] = preparePaginationRange(args);

  const { data: invitations, count } = await supabase
    .from("invitations")
    .select("*", { count: "exact" })
    .ilike("email", userEmail)
    .is("accepted_at", null)
    .is("deleted_at", null)
    .gt("expires_at", new Date().toISOString())
    .range(start, end);

  return buildConnectionOrEmpty(invitations, args, count);
}

export async function requireOrganizationAccess(
  userId: string,
  orgId: string,
): Promise<any> {
  const org = await getOrganization(orgId);
  await requireOrgMembership(userId, org.id);
  return org;
}

export async function getResourceById<T>(params: {
  tableName: keyof Database["public"]["Tables"];
  id: string;
  userId: string;
  checkMembership?: boolean;
}): Promise<T | null> {
  const { tableName, id, userId, checkMembership = true } = params;

  const supabase = createAdminClient();
  const { data: resource, error } = await supabase
    .from(tableName)
    .select("*")
    .eq("id", id)
    .is("deleted_at", null)
    .single();

  if (error || !resource) {
    return null;
  }

  if (checkMembership && "org_id" in resource && resource.org_id) {
    try {
      await requireOrgMembership(userId, resource.org_id as string);
      return resource as T;
    } catch {
      return null;
    }
  }

  return resource as T;
}

export async function checkMembershipExists(
  userId: string,
  orgId: string,
): Promise<boolean> {
  const supabase = createAdminClient();

  const { data: existingMembership } = await supabase
    .from("users_by_organization")
    .select("*")
    .eq("user_id", userId)
    .eq("org_id", orgId)
    .is("deleted_at", null)
    .single();

  return !!existingMembership;
}
