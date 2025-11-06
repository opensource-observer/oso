import { createAdminClient } from "@/lib/supabase/admin";
import {
  buildConnection,
  emptyConnection,
  type Connection,
} from "@/app/api/v1/osograph/utils/connection";
import type { ConnectionArgs } from "@/app/api/v1/osograph/utils/pagination";
import {
  getFetchLimit,
  getSupabaseRange,
} from "@/app/api/v1/osograph/utils/pagination";
import {
  getOrganization,
  requireOrgMembership,
} from "@/app/api/v1/osograph/utils/auth";
import { Database } from "@/lib/types/supabase";

export function preparePaginationRange(args: ConnectionArgs): [number, number] {
  const limit = getFetchLimit(args);
  return getSupabaseRange({
    ...args,
    first: limit,
  });
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

export async function getNotebooksConnection(
  orgIds: string | string[],
  args: ConnectionArgs,
): Promise<Connection<any>> {
  const supabase = createAdminClient();
  const orgIdArray = Array.isArray(orgIds) ? orgIds : [orgIds];

  if (orgIdArray.length === 0) {
    return emptyConnection();
  }

  const [start, end] = preparePaginationRange(args);

  const query = supabase
    .from("notebooks")
    .select("*", { count: "exact" })
    .is("deleted_at", null)
    .range(start, end);

  const { data: notebooks, count } =
    orgIdArray.length === 1
      ? await query.eq("org_id", orgIdArray[0])
      : await query.in("org_id", orgIdArray);

  return buildConnectionOrEmpty(notebooks, args, count);
}

export async function getDatasetsConnection(
  orgIds: string | string[],
  args: ConnectionArgs,
): Promise<Connection<any>> {
  const supabase = createAdminClient();
  const orgIdArray = Array.isArray(orgIds) ? orgIds : [orgIds];

  if (orgIdArray.length === 0) {
    return emptyConnection();
  }

  const [start, end] = preparePaginationRange(args);

  const query = supabase
    .from("datasets")
    .select("*", { count: "exact" })
    .is("deleted_at", null)
    .range(start, end);

  const { data: datasets, count } =
    orgIdArray.length === 1
      ? await query.eq("org_id", orgIdArray[0])
      : await query.in("org_id", orgIdArray);

  return buildConnectionOrEmpty(datasets, args, count);
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

export async function getResourceByIdOrName<T>(params: {
  tableName: keyof Database["public"]["Tables"];
  args: { id?: string; name?: string };
  userId: string;
  checkMembership?: boolean;
}): Promise<T | null> {
  const { tableName, args, userId, checkMembership = true } = params;

  if (!args.id && !args.name) {
    return null;
  }

  const supabase = createAdminClient();
  let query = supabase.from(tableName).select("*").is("deleted_at", null);

  if (args.id) {
    query = query.eq("id", args.id);
  } else if (args.name) {
    query = query.eq("name", args.name);
  }

  const { data: resource, error } = await query.single();

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
