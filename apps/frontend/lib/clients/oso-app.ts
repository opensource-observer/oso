import _ from "lodash";
import { SupabaseClient } from "@supabase/supabase-js";
import { supabaseClient as defaultClient } from "./supabase";
import { Database, Tables } from "../types/supabase";
import { MissingDataError, AuthError } from "../types/errors";
import { ensure } from "@opensource-observer/utils";

/**
 * OsoAppClient is the client library for the OSO app.
 * It provides the read/write functionality.
 * - Note that all method arguments are a single Partial object.
 * - This is to make it easier to pass arguments from Plasmic Studio,
 *   but it does mean we need to validate arguments
 */
class OsoAppClient {
  private supabaseClient: SupabaseClient<Database>;

  /**
   * Pass in an explicit supabase client
   * Otherwise default to the one stored as a global
   * @param inboundClient
   */
  constructor(inboundClient?: SupabaseClient<Database>) {
    this.supabaseClient = inboundClient || defaultClient;
  }

  /**
   * Gets the current user from the Supabase client.
   * @returns
   */
  async getUser() {
    const { data, error } = await this.supabaseClient.auth.getUser();
    if (error) {
      throw error;
    } else if (!data) {
      throw new AuthError("Not logged in");
    }
    return data.user;
  }

  /**
   * Gets the current logged in user profile.
   * @returns
   */
  async getMyUserProfile() {
    const user = await this.getUser();
    const { data, error } = await this.supabaseClient
      .from("user_profiles")
      .select("*")
      .eq("id", user.id)
      .single();
    if (error) {
      throw error;
    } else if (!data) {
      throw new MissingDataError(
        `Unable to find user profile for id=${user.id}`,
      );
    }
    return data;
  }

  /**
   * Updates the current logged in user profile.
   * @param profile
   */
  async updateMyUserProfile(
    args: Partial<{
      profile: Partial<Tables<"user_profiles">>;
    }>,
  ) {
    const profile = ensure(args.profile, "Missing profile argument");
    const user = await this.getUser();
    const { error } = await this.supabaseClient
      .from("user_profiles")
      .update({ ...profile, id: user.id })
      .eq("id", user.id);
    if (error) {
      throw error;
    }
  }

  /**
   * Creates a new API key for the current user.
   * - Relies on DB column constraints/triggers to ensure API key constraints
   * @param keyData
   */
  async createApiKey(
    args: Partial<{
      name: string;
      apiKey: string;
    }>,
  ) {
    const name = ensure(args.name, "Missing name argument");
    const apiKey = ensure(args.apiKey, "Missing apiKey argument");
    const user = await this.getUser();
    const { error } = await this.supabaseClient.from("api_keys").insert({
      name,
      api_key: apiKey,
      user_id: user.id,
    });
    if (error) {
      throw error;
    }
  }

  /**
   * Creates a new organization
   * @param orgName
   */
  async createOrganization(
    args: Partial<{
      orgName: string;
    }>,
  ) {
    const orgName = ensure(args.orgName, "Missing orgName argument");
    const user = await this.getUser();
    const { error } = await this.supabaseClient.from("organizations").insert({
      org_name: orgName,
      created_by: user.id,
    });
    if (error) {
      throw error;
    }
  }

  /**
   * Gets all organizations for the current user.
   * @returns
   */
  async getMyOrganizations() {
    const user = await this.getUser();
    // Get the organizations that the user has created
    const { data: createdOrgs, error: createdError } = await this.supabaseClient
      .from("organizations")
      .select("id")
      .eq("created_by", user.id)
      .is("deleted_at", null);
    // Get the organizations that the user has joined
    const { data: joinedOrgs, error: joinedError } = await this.supabaseClient
      .from("users_by_organization")
      .select("org_id")
      .eq("user_id", user.id)
      .is("deleted_at", null);
    // Get all organization details
    const orgIds = [
      ...(createdOrgs ?? []).map((org) => org.id),
      ...(joinedOrgs ?? []).map((org) => org.org_id),
    ];
    const { data, error: orgError } = await this.supabaseClient
      .from("organizations")
      .select("*")
      .in("id", orgIds)
      .is("deleted_at", null);
    if (createdError || joinedError || orgError) {
      throw createdError || joinedError || orgError;
    }
    if (!data) {
      throw new MissingDataError(
        `Unable to find organizations for user id=${user.id}`,
      );
    }
    return data;
  }

  /**
   * Gets the organization details by id.
   * @param orgId
   * @returns
   */
  async getOrganizationById(
    args: Partial<{
      orgId: string;
    }>,
  ) {
    const orgId = ensure(args.orgId, "Missing orgId argument");
    const { data, error } = await this.supabaseClient
      .from("organizations")
      .select("*")
      .eq("id", orgId)
      .single();
    if (error) {
      throw error;
    } else if (!data) {
      throw new MissingDataError(
        `Unable to find organization with id=${orgId}`,
      );
    }
    return data;
  }

  /**
   * Gets all users in an organization.
   * @param orgId
   * @returns
   */
  async getOrganizationMembers(
    args: Partial<{
      orgId: string;
    }>,
  ) {
    const orgId = ensure(args.orgId, "Missing orgId argument");
    // Get the owner/creator of the organization
    const { data: creatorData, error: creatorError } = await this.supabaseClient
      .from("organizations")
      .select("created_by")
      .eq("id", orgId);
    // Get the members of the organization
    const { data: memberData, error: memberError } = await this.supabaseClient
      .from("users_by_organization")
      .select("user_id, user_role")
      .eq("org_id", orgId)
      .is("deleted_at", null);
    // Map the user ids to their roles
    const userRoleMap = _.fromPairs([
      ...(creatorData ?? []).map((x) => [x.created_by, "owner"]),
      ...(memberData ?? []).map((x) => [x.user_id, x.user_role]),
    ]);
    // Get all user profiles
    const { data: userData, error: userError } = await this.supabaseClient
      .from("user_profiles")
      .select("*")
      .in("id", _.keys(userRoleMap))
      .is("deleted_at", null);
    if (creatorError || memberError || userError) {
      throw creatorError || memberError || userError;
    } else if (!userData) {
      throw new MissingDataError(
        `Unable to find members for organization id=${orgId}`,
      );
    }
    // Make sure to include the `user_role`
    const result = userData.map((user) => ({
      ...user,
      user_role: userRoleMap[user.id],
    }));
    return result;
  }

  /**
   * Adds a user to an organization.
   */
  async addUserToOrganizationByEmail(
    args: Partial<{
      orgId: string;
      email: string;
      role: string;
    }>,
  ) {
    const orgId = ensure(args.orgId, "Missing orgId argument");
    const email = ensure(args.email, "Missing email argument");
    const role = ensure(args.role, "Missing role argument");
    const { data: profileData, error: profileError } = await this.supabaseClient
      .from("user_profiles")
      .select("*")
      .eq("email", email);
    if (profileError) {
      throw profileError;
    } else if (!profileData || profileData.length === 0) {
      throw new MissingDataError(
        `Unable to find user profile for email=${email}`,
      );
    }
    const userId = profileData[0].id;
    // Get the members of the organization
    const { error } = await this.supabaseClient
      .from("users_by_organization")
      .insert({ org_id: orgId, user_id: userId, user_role: role });
    if (error) {
      throw error;
    }
  }

  /**
   * Updates the user role in an organization.
   * @param orgId
   * @param userId
   * @param role
   */
  async changeUserRole(
    args: Partial<{
      orgId: string;
      userId: string;
      role: string;
    }>,
  ) {
    const orgId = ensure(args.orgId, "Missing orgId argument");
    const userId = ensure(args.userId, "Missing userId argument");
    const role = ensure(args.role, "Missing role argument");
    const { error } = await this.supabaseClient
      .from("users_by_organization")
      .update({ user_role: role })
      .eq("user_id", userId)
      .eq("org_id", orgId)
      .is("deleted_at", null);
    if (error) {
      throw error;
    }
  }

  /**
   * Removes a user from an organization.
   * - We use `deleted_at` to mark the user as removed instead of deleting the row
   * @param orgId
   * @param userId
   */
  async removeUserFromOrganization(
    args: Partial<{
      orgId: string;
      userId: string;
    }>,
  ) {
    const orgId = ensure(args.orgId, "Missing orgId argument");
    const userId = ensure(args.userId, "Missing userId argument");
    const { error } = await this.supabaseClient
      .from("users_by_organization")
      .update({ deleted_at: new Date().toISOString() })
      .eq("org_id", orgId)
      .eq("user_id", userId);
    if (error) {
      throw error;
    }
  }

  /**
   * Removes an organization.
   * - We use `deleted_at` to mark the organization as removed instead of deleting the row
   * @param orgId
   */
  async deleteOrganization(
    args: Partial<{
      orgId: string;
    }>,
  ) {
    const orgId = ensure(args.orgId, "Missing orgId argument");
    const { error } = await this.supabaseClient
      .from("organizations")
      .update({ deleted_at: new Date().toISOString() })
      .eq("id", orgId);
    if (error) {
      throw error;
    }
  }
}

export { OsoAppClient };
