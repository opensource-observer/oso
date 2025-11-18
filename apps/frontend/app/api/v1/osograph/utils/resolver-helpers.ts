import { createAdminClient } from "@/lib/supabase/admin";
import {
  buildConnection,
  type Connection,
  emptyConnection,
} from "@/app/api/v1/osograph/utils/connection";
import type {
  ConnectionArgs,
  FilterableConnectionArgs,
} from "@/app/api/v1/osograph/utils/pagination";
import {
  getFetchLimit,
  getPaginationParams,
} from "@/app/api/v1/osograph/utils/pagination";
import {
  getOrganization,
  requireOrgMembership,
} from "@/app/api/v1/osograph/utils/auth";
import { Database } from "@/lib/types/supabase";
import {
  buildQuery,
  mergePredicates,
  type QueryPredicate,
} from "@/app/api/v1/osograph/utils/query-builder";
import { ServerErrors } from "@/app/api/v1/osograph/utils/errors";

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
  args: FilterableConnectionArgs,
  additionalPredicate?: Partial<QueryPredicate<"organizations">>,
) {
  const supabase = createAdminClient();
  const [start, end] = preparePaginationRange(args);

  const membershipPredicate: Partial<QueryPredicate<"users_by_organization">> =
    {
      eq: [{ key: "user_id", value: userId }],
      is: [{ key: "deleted_at", value: null }],
    };

  const {
    data: memberships,
    count: membershipCount,
    error: membershipError,
  } = await buildQuery(
    supabase,
    "users_by_organization",
    membershipPredicate,
    (query) => query.range(start, end),
  );

  if (membershipError) {
    throw ServerErrors.database(
      `Failed to fetch memberships: ${membershipError.message}`,
    );
  }

  if (!memberships || memberships.length === 0) {
    return emptyConnection();
  }

  const orgIds = memberships.map((m) => m.org_id);

  const basePredicate: Partial<QueryPredicate<"organizations">> = {
    in: [{ key: "id", value: orgIds }],
  };

  const predicate = additionalPredicate
    ? mergePredicates(basePredicate, additionalPredicate)
    : basePredicate;

  const { data: organizations, error: orgError } = await buildQuery(
    supabase,
    "organizations",
    predicate,
    undefined,
    args.single,
  );

  if (orgError) {
    throw ServerErrors.database(
      `Failed to fetch organizations: ${orgError.message}`,
    );
  }

  return buildConnectionOrEmpty(organizations, args, membershipCount);
}

export async function getUserInvitationsConnection(
  email: string | null | undefined,
  args: ConnectionArgs,
  additionalPredicate?: Partial<QueryPredicate<"invitations">>,
) {
  if (!email) {
    return emptyConnection();
  }

  const supabase = createAdminClient();
  const userEmail = email.toLowerCase();
  const [start, end] = preparePaginationRange(args);

  const basePredicate: Partial<QueryPredicate<"invitations">> = {
    ilike: [{ key: "email", value: userEmail }],
    is: [
      { key: "accepted_at", value: null },
      { key: "deleted_at", value: null },
    ],
    gt: [{ key: "expires_at", value: new Date().toISOString() }],
  };

  const predicate = additionalPredicate
    ? mergePredicates(basePredicate, additionalPredicate)
    : basePredicate;

  const {
    data: invitations,
    count,
    error,
  } = await buildQuery(supabase, "invitations", predicate, (query) =>
    query.range(start, end),
  );

  if (error) {
    throw ServerErrors.database(
      `Failed to fetch invitations: ${error.message}`,
    );
  }

  return buildConnectionOrEmpty(invitations, args, count);
}

export async function requireOrganizationAccess(userId: string, orgId: string) {
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
