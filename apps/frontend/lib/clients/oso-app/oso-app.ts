import _ from "lodash";
import { v4 as uuid4 } from "uuid";
import { SupabaseClient } from "@supabase/supabase-js";
import { assert, ensure } from "@opensource-observer/utils";
import { Database, Tables } from "@/lib/types/supabase";
import { MissingDataError, AuthError } from "@/lib/types/errors";
import { logger } from "@/lib/logger";
import { gql } from "@/lib/graphql/generated/gql";
import { print } from "graphql";
import {
  resourcePermissionResponseSchema,
  type ResourcePermissionResponse,
} from "@/lib/types/permissions";
import {
  dynamicColumnContextsRowSchema,
  dynamicConnectorsInsertSchema,
  dynamicConnectorsRowSchema,
  dynamicTableContextsRowSchema,
  connectorRelationshipsInsertSchema,
} from "@/lib/types/schema";
import type {
  ConnectorRelationshipsRow,
  ConnectorRelationshipsInsert,
  DynamicColumnContextsRow,
  DynamicConnectorsInsert,
  DynamicConnectorsRow,
  DynamicTableContextsRow,
} from "@/lib/types/schema-types";
import { NotebookKey } from "@/lib/types/db";
import { CREDIT_PACKAGES } from "@/lib/clients/stripe";
import { DEFAULT_OSO_TABLE_ID } from "@/lib/types/dynamic-connector";
import {
  uniqueNamesGenerator,
  adjectives,
  animals,
} from "unique-names-generator";
import { DatasetType } from "@/lib/types/dataset";

const ADMIN_USER_ROLE = "admin";

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
  constructor(inboundClient: SupabaseClient<Database>) {
    this.supabaseClient = inboundClient;
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
    console.log("getMyUserProfile");
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
    console.log("updateMyUserProfile: ", args);
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
      orgName: string;
    }>,
  ) {
    console.log("createApiKey: ", args.name);
    const name = ensure(args.name, "Missing name argument");
    const apiKey = ensure(args.apiKey, "Missing apiKey argument");
    const orgName = ensure(args.orgName, "Missing orgName argument");
    const user = await this.getUser();
    const org = await this.getOrganizationByName({ orgName });
    const { error } = await this.supabaseClient.from("api_keys").insert({
      name,
      api_key: apiKey,
      user_id: user.id,
      org_id: org.id,
    });
    if (error) {
      throw error;
    }
  }

  /**
   * Gets the current logged in user's API keys
   * @returns
   */
  async getMyApiKeys() {
    console.log("getMyApiKeys");
    const user = await this.getUser();
    const { data, error } = await this.supabaseClient
      .from("api_keys")
      .select("id, name, created_at, org_id")
      .eq("user_id", user.id)
      .is("deleted_at", null);
    if (error) {
      throw error;
    } else if (!data) {
      throw new MissingDataError(`Unable to find API keys for id=${user.id}`);
    }
    return data;
  }

  async getApiKeysByOrgName(args: { orgName: string }) {
    const orgName = ensure(args.orgName, "Missing orgName argument");
    const { data, error } = await this.supabaseClient
      .from("api_keys")
      .select(
        "id, name, user_id, created_at, org_id, organizations!inner(org_name)",
      )
      .eq("organizations.org_name", orgName)
      .is("deleted_at", null);
    if (error) {
      throw error;
    } else if (!data) {
      throw new MissingDataError(
        `Unable to find API keys for org_name=${orgName}`,
      );
    }
    return data;
  }

  /**
   * Removes an API Key
   * - We use `deleted_at` to mark the key as removed instead of deleting the row
   * @param orgId
   */
  async deleteApiKeyById(
    args: Partial<{
      keyId: string;
    }>,
  ) {
    console.log("deleteApiKeyById: ", args);
    const keyId = ensure(args.keyId, "Missing keyId argument");
    const { error } = await this.supabaseClient
      .from("api_keys")
      .update({ deleted_at: new Date().toISOString() })
      .eq("id", keyId);
    if (error) {
      throw error;
    }
  }

  async getOsoJwt(
    args: Partial<{ orgName: string }>,
  ): Promise<{ token: string }> {
    const orgName = ensure(args.orgName, "Missing orgName argument");

    const searchParams = new URLSearchParams({ orgName });

    const response = await fetch(`/api/v1/jwt?${searchParams.toString()}`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(`Error fetching JWT: ${error?.error ?? error}`);
    }
    const result = await response.json();
    ensure(result.token, "Missing token in response");
    return result;
  }

  /**
   * Creates a new organization and adds the creator as admin member
   * @param orgName
   */
  async createOrganization(
    args: Partial<{
      orgName: string;
    }>,
  ) {
    console.log("createOrganization: ", args);
    const orgName = ensure(args.orgName, "Missing orgName argument");
    const user = await this.getUser();

    const { data: orgData } = await this.supabaseClient
      .from("organizations")
      .insert({
        org_name: orgName,
        created_by: user.id,
      })
      .select()
      .single()
      .throwOnError();

    if (!orgData) {
      throw new MissingDataError("Failed to create organization");
    }

    return orgData;
  }

  /**
   * Gets all organizations for the current user.
   * @returns
   */
  async getMyOrganizations() {
    console.log("getMyOrganizations");
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
    console.log("getOrganizationById: ", args);
    const orgId = ensure(args.orgId, "Missing orgId argument");
    const { data, error } = await this.supabaseClient
      .from("organizations")
      .select("*,pricing_plan!inner(plan_name)")
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
   * Gets the organization details by org_name.
   * @param orgName
   * @returns
   */
  async getOrganizationByName(
    args: Partial<{
      orgName: string;
    }>,
  ) {
    console.log("getOrganizationByName: ", args);
    const orgName = ensure(args.orgName, "Missing orgName argument");
    const { data, error } = await this.supabaseClient
      .from("organizations")
      .select("*,pricing_plan!inner(plan_name)")
      .eq("org_name", orgName)
      .single();
    if (error) {
      throw error;
    } else if (!data) {
      throw new MissingDataError(
        `Unable to find organization with org_name=${orgName}`,
      );
    }
    return data;
  }

  /**
   * Gets all users in an organization.
   * @param orgName
   * @returns
   */
  async getOrganizationMembers(
    args: Partial<{
      orgName: string;
    }>,
  ) {
    console.log("getOrganizationMembers: ", args);
    const orgName = ensure(args.orgName, "Missing orgName argument");
    // Get the members of the organization
    const { data: memberData, error: memberError } = await this.supabaseClient
      .from("users_by_organization")
      .select("*,organizations!inner(org_name, created_by)")
      .eq("organizations.org_name", orgName)
      .is("deleted_at", null);
    // Map the user ids to their roles
    const userRoleMap = _.fromPairs([
      ...(memberData ?? []).map((x) => [
        x.organizations.created_by,
        ADMIN_USER_ROLE,
      ]),
      ...(memberData ?? []).map((x) => [x.user_id, x.user_role]),
    ]);
    // Get all user profiles
    const { data: userData, error: userError } = await this.supabaseClient
      .from("user_profiles")
      .select("*")
      .in("id", _.keys(userRoleMap));
    if (memberError || userError) {
      throw memberError || userError;
    } else if (!userData) {
      throw new MissingDataError(
        `Unable to find members for organization org_name=${orgName}`,
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
      orgName: string;
      email: string;
      role: string;
    }>,
  ) {
    console.log("addUserToOrganizationByEmail: ", args);
    const orgName = ensure(args.orgName, "Missing orgName argument");
    const email = ensure(args.email, "Missing email argument");
    const role = ensure(args.role, "Missing role argument");
    const org = await this.getOrganizationByName({ orgName });
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
      .insert({ org_id: org.id, user_id: userId, user_role: role });
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
    console.log("changeUserRole: ", args);
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
   * @param orgName
   * @param userId
   */
  async removeUserFromOrganization(
    args: Partial<{
      orgName: string;
      userId: string;
    }>,
  ) {
    console.log("removeUserFromOrganization: ", args);
    const orgName = ensure(args.orgName, "Missing orgId argument");
    const userId = ensure(args.userId, "Missing userId argument");
    const org = await this.getOrganizationByName({ orgName });
    const deletedAt = new Date().toISOString();
    const { error: orgError } = await this.supabaseClient
      .from("users_by_organization")
      .update({ deleted_at: deletedAt })
      .eq("org_id", org.id)
      .eq("user_id", userId);
    if (orgError) {
      throw orgError;
    }
    const { error: apiKeyError } = await this.supabaseClient
      .from("api_keys")
      .update({ deleted_at: deletedAt })
      .eq("org_id", org.id)
      .eq("user_id", userId);
    if (apiKeyError) {
      throw apiKeyError;
    }
  }

  /**
   * Removes an organization.
   * - We use `deleted_at` to mark the organization as removed instead of deleting the row
   * @param orgName
   */
  async deleteOrganizationByName(
    args: Partial<{
      orgName: string;
    }>,
  ) {
    console.log("deleteOrganizationByName: ", args);
    const orgName = ensure(args.orgName, "Missing orgName argument");
    const { error } = await this.supabaseClient
      .from("organizations")
      .update({ deleted_at: new Date().toISOString() })
      .eq("org_name", orgName);
    if (error) {
      throw error;
    }
  }

  /**
   * Creates a new chat session
   * - Chats are stored under an organization
   * @param args
   * @returns
   */
  async createChat(args: Partial<{ orgName: string; displayName: string }>) {
    console.log("createChat: ", args);
    const orgName = ensure(args.orgName, "Missing orgName argument");
    const displayName = args.displayName || new Date().toLocaleString();
    const user = await this.getUser();
    const org = await this.getOrganizationByName({ orgName });

    const { data: chatData, error: chatError } = await this.supabaseClient
      .from("chat_history")
      .insert({
        org_id: org.id,
        display_name: displayName,
        created_by: user.id,
      })
      .select()
      .single();

    if (chatError) {
      throw chatError;
    } else if (!chatData) {
      throw new MissingDataError("Failed to create chat");
    }

    return chatData;
  }

  async getChatsByOrgName(args: Partial<{ orgName: string }>) {
    console.log("getChatsByOrgName: ", args);
    const orgName = ensure(args.orgName, "Missing orgName argument");
    const { data, error } = await this.supabaseClient
      .from("chat_history")
      .select("*,organizations!inner(org_name)")
      .eq("organizations.org_name", orgName)
      .is("deleted_at", null);
    if (error) {
      throw error;
    } else if (!data) {
      throw new MissingDataError(`Unable to find chats for orgName=${orgName}`);
    }
    return data;
  }

  async getChatById(args: Partial<{ chatId: string }>) {
    console.log("getChatById: ", args);
    const chatId = ensure(args.chatId, "Missing chatId argument");
    const { data, error } = await this.supabaseClient
      .from("chat_history")
      .select()
      .eq("id", chatId)
      .is("deleted_at", null)
      .single();
    if (error) {
      throw error;
    } else if (!data) {
      throw new MissingDataError(`Unable to find chat for chatId=${chatId}`);
    }
    return data;
  }

  /**
   * Update chat data
   * @param args
   */
  async updateChat(
    args: Partial<Database["public"]["Tables"]["chat_history"]["Update"]>,
  ) {
    console.log("updateChat: ", args);
    const chatId = ensure(args.id, "Missing chat 'id' argument");
    const { error } = await this.supabaseClient
      .from("chat_history")
      .update({ ...args })
      .eq("id", chatId);
    if (error) {
      throw error;
    }
  }

  /**
   * Removes a chat
   * - We use `deleted_at` to mark the chat as removed instead of deleting the row
   * @param args
   */
  async deleteChatById(args: Partial<{ chatId: string }>): Promise<void> {
    console.log("deleteChatById: ", args);
    const chatId = ensure(args.chatId, "Missing chatId argument");
    const { error } = await this.supabaseClient
      .from("chat_history")
      .update({ deleted_at: new Date().toISOString() })
      .eq("id", chatId);
    if (error) {
      throw error;
    }
  }

  private randomNotebookName() {
    return uniqueNamesGenerator({
      dictionaries: [adjectives, animals],
      length: 2,
      separator: "_",
    });
  }

  /**
   * Creates a new notebook
   * - Notebooks are stored under an organization
   * @param args
   * @returns
   */
  async createNotebook(args: Partial<NotebookKey>) {
    console.log("createNotebook: ", args);
    const orgName = ensure(args.orgName, "Missing orgName argument");
    const notebookName = args.notebookName || this.randomNotebookName();
    const user = await this.getUser();
    const org = await this.getOrganizationByName({ orgName });

    const { data: queryData, error: queryError } = await this.supabaseClient
      .from("notebooks")
      .insert({
        org_id: org.id,
        notebook_name: notebookName,
        created_by: user.id,
      })
      .select()
      .single();

    if (queryError) {
      throw queryError;
    } else if (!queryData) {
      throw new MissingDataError("Failed to create notebook");
    }

    return queryData;
  }

  /**
   * Forks an existing notebook to create a new one
   * - For now just copies the data
   * - Notebooks are stored under an organization
   * @param source.orgName
   * @param source.notebookName
   * @param destination.orgName
   * @param destination.notebookName - optional, will auto-generate if not provided
   * @returns
   */
  async forkNotebook(
    args: Partial<{
      source: Partial<NotebookKey>;
      destination: Partial<NotebookKey>;
    }>,
  ) {
    console.log("forkNotebook: ", args);
    const srcOrgName = ensure(
      args.source?.orgName,
      "Missing source.orgName argument",
    );
    const srcNotebookName = ensure(
      args.source?.notebookName,
      "Missing source.notebookName argument",
    );
    const dstOrgName = ensure(
      args.destination?.orgName,
      "Missing destination.orgName argument",
    );
    const dstNotebookName =
      args.destination?.notebookName ||
      `copy_${srcNotebookName}_${uuid4().substring(0, 5)}`;
    const dstOrg = await this.getOrganizationByName({ orgName: dstOrgName });
    const srcNotebook = await this.getNotebookByName({
      orgName: srcOrgName,
      notebookName: srcNotebookName,
    });
    const user = await this.getUser();

    const { data: queryData, error: queryError } = await this.supabaseClient
      .from("notebooks")
      .insert({
        org_id: dstOrg.id,
        notebook_name: dstNotebookName,
        created_by: user.id,
        data: srcNotebook.data,
      })
      .select()
      .single();

    if (queryError) {
      throw queryError;
    } else if (!queryData) {
      throw new MissingDataError("Failed to create notebook");
    }

    return queryData;
  }

  async getNotebooksByOrgName(args: Partial<{ orgName: string }>) {
    console.log("getNotebooksByOrgName: ", args);
    const orgName = ensure(args.orgName, "Missing orgName argument");
    const { data, error } = await this.supabaseClient
      .from("notebooks")
      .select(
        "id,created_at,updated_at,notebook_name,organizations!inner(id,org_name)",
      )
      .eq("organizations.org_name", orgName)
      .is("deleted_at", null);
    if (error) {
      throw error;
    } else if (!data) {
      throw new MissingDataError(
        `Unable to find notebooks for orgName=${orgName}`,
      );
    }
    return data;
  }

  async listNotebooksByOrgName(args: Partial<{ orgName: string }>) {
    return await this.getNotebooksByOrgName(args);
  }

  async getNotebookById(args: Partial<{ notebookId: string }>) {
    console.log("getNotebookById: ", args);
    const notebookId = ensure(args.notebookId, "Missing notebookId argument");
    const { data, error } = await this.supabaseClient
      .from("notebooks")
      .select()
      .eq("id", notebookId)
      .is("deleted_at", null)
      .single();
    if (error) {
      throw error;
    } else if (!data) {
      throw new MissingDataError(
        `Unable to find notebook for notebookId=${notebookId}`,
      );
    }
    return data;
  }

  async getNotebookByName(args: Partial<NotebookKey>) {
    console.log("getNotebookByName: ", args);
    const orgName = ensure(args.orgName, "Missing orgName argument");
    const notebookName = ensure(
      args.notebookName,
      "Missing notebookName argument",
    );
    const { data, error } = await this.supabaseClient
      .from("notebooks")
      .select("*,organizations!inner(org_name)")
      .eq("organizations.org_name", orgName)
      .eq("notebook_name", notebookName)
      .is("deleted_at", null)
      .single();
    if (error) {
      throw error;
    } else if (!data) {
      throw new MissingDataError(
        `Unable to find notebook for orgName=${orgName}, notebookName=${notebookName}`,
      );
    }
    return data;
  }

  /**
   * Moves a notebook
   * - Could be within the same org or to a different org
   * @param source.orgName
   * @param source.notebookName
   * @param destination.orgName
   * @param destination.notebookName
   */
  async moveNotebook(
    args: Partial<{
      source: Partial<NotebookKey>;
      destination: Partial<NotebookKey>;
    }>,
  ) {
    console.log("moveNotebook: ", args);
    const srcOrgName = ensure(
      args.source?.orgName,
      "Missing source.orgName argument",
    );
    const srcNotebookName = ensure(
      args.source?.notebookName,
      "Missing source.notebookName argument",
    );
    const dstOrgName = ensure(
      args.destination?.orgName,
      "Missing destination.orgName argument",
    );
    const dstNotebookName = ensure(
      args.destination?.notebookName,
      "Missing destination.notebookName argument",
    );
    const dstOrg = await this.getOrganizationByName({ orgName: dstOrgName });
    const srcNotebook = await this.getNotebookByName({
      orgName: srcOrgName,
      notebookName: srcNotebookName,
    });
    const { error } = await this.supabaseClient
      .from("notebooks")
      .update({ org_id: dstOrg.id, notebook_name: dstNotebookName })
      .eq("id", srcNotebook.id);
    if (error) {
      throw error;
    }
  }

  /**
   * Update notebook data
   * @param args
   */
  async updateNotebook(
    args: Partial<Database["public"]["Tables"]["notebooks"]["Update"]>,
  ) {
    console.log("updateNotebook: ", args);
    const notebookId = ensure(args.id, "Missing notebook 'id' argument");
    const { error } = await this.supabaseClient
      .from("notebooks")
      .update({ ...args })
      .eq("id", notebookId);
    if (error) {
      throw error;
    }
  }

  /**
   * Removes a notebook
   * - We use `deleted_at` to mark the notebook as removed instead of deleting the row
   * @param args
   */
  async deleteNotebookById(
    args: Partial<{ notebookId: string }>,
  ): Promise<void> {
    console.log("deleteNotebookById: ", args);
    const notebookId = ensure(args.notebookId, "Missing notebookId argument");
    const { error } = await this.supabaseClient
      .from("notebooks")
      .update({ deleted_at: new Date().toISOString() })
      .eq("id", notebookId);
    if (error) {
      throw error;
    }
  }

  async publishNotebook(args: Partial<{ notebookId: string }>) {
    console.log("publishNotebook: ", args);
    const notebookId = ensure(args.notebookId, "Missing notebookId argument");
    const response = await fetch("/api/v1/notebooks/publish", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ notebookId }),
    });
    const json = await response.json();
    if (!response.ok) {
      throw new Error("Error publishing notebook: " + json.error);
    }
    return true;
  }

  async unpublishNotebook(args: Partial<{ notebookId: string }>) {
    console.log("unpublishNotebook: ", args);
    const notebookId = ensure(args.notebookId, "Missing notebookId argument");
    const response = await fetch("/api/v1/notebooks/publish", {
      method: "DELETE",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ notebookId }),
    });
    const json = await response.json();
    if (!response.ok) {
      throw new Error("Error unpublishing notebook: " + json.error);
    }
    return true;
  }

  /**
   * Gets the current credit balance for an organization.
   * @param orgName - The unique organization name
   * @returns Promise<number> - The current credit balance
   */
  async getOrganizationCredits(
    args: Partial<{ orgName: string }>,
  ): Promise<number> {
    const orgName = ensure(
      args.orgName,
      "orgName is required to get organization credits",
    );
    console.log("getOrganizationCredits for orgName=", orgName);
    const { data, error } = await this.supabaseClient
      .from("organization_credits")
      .select("credits_balance, organizations!inner(org_name)")
      .eq("organizations.org_name", orgName)
      .single();

    if (error) {
      throw error;
    } else if (!data) {
      throw new MissingDataError(
        `Unable to find credits for organization orgName=${orgName}`,
      );
    }
    return data.credits_balance;
  }

  /**
   * Gets subscription and billing status for an organization.
   * @param orgName
   * @returns Promise<SubscriptionStatus>
   */
  async getSubscriptionStatus(args: Partial<{ orgName: string }>) {
    const orgName = ensure(
      args.orgName,
      "orgName is required to get subscription status",
    );

    const { data } = await this.supabaseClient
      .from("organizations")
      .select(
        `
        id,
        org_name,
        created_at,
        enterprise_support_url,
        billing_contact_email,
        pricing_plan(
          plan_id,
          plan_name,
          price_per_credit,
          max_credits_per_cycle,
          refill_cycle_days
        ),
        organization_credits(
          credits_balance,
          last_refill_at,
          created_at,
          updated_at
        )
      `,
      )
      .eq("org_name", orgName)
      .maybeSingle()
      .throwOnError();

    if (!data) {
      throw new MissingDataError(
        `Unable to find subscription status for organization orgName=${orgName}`,
      );
    }

    const credits = data.organization_credits;
    const plan = data.pricing_plan;

    const lastRefill = credits?.last_refill_at
      ? new Date(credits.last_refill_at)
      : null;
    const cycleStartDate = lastRefill;
    const cycleEndDate =
      lastRefill && plan.refill_cycle_days
        ? new Date(
            lastRefill.getTime() + plan.refill_cycle_days * 24 * 60 * 60 * 1000,
          )
        : null;

    const daysUntilRefill = cycleEndDate
      ? Math.max(
          0,
          Math.ceil(
            (cycleEndDate.getTime() - Date.now()) / (24 * 60 * 60 * 1000),
          ),
        )
      : 0;

    const isEnterprise = plan.plan_name === "ENTERPRISE";
    const isFree = plan.plan_name === "FREE";
    const isActive = true;

    const features = {
      maxCreditsPerCycle: plan.max_credits_per_cycle || 0,
      refillCycleDays: plan.refill_cycle_days || 0,
      pricePerCredit: plan.price_per_credit || 0,
      hasUnlimitedQueries: isEnterprise,
      hasPrioritySupport: isEnterprise,
      hasAdvancedAnalytics: isEnterprise,
      canCreateCustomConnectors: isEnterprise,
    };

    const finalCreditsBalance = credits?.credits_balance || 0;

    return {
      orgId: data.id,
      orgName: data.org_name,
      planId: plan.plan_id,
      planName: plan.plan_name,
      planDescription: undefined,
      tier: plan.plan_name.toLowerCase(),
      creditsBalance: finalCreditsBalance,
      maxCreditsPerCycle: plan.max_credits_per_cycle || 0,
      billingCycle: {
        cycleDays: plan.refill_cycle_days || 0,
        cycleStartDate: cycleStartDate?.toISOString() || null,
        cycleEndDate: cycleEndDate?.toISOString() || null,
        daysUntilRefill,
        lastRefillAt: lastRefill?.toISOString() || null,
      },
      subscriptionStatus: {
        isActive,
        isEnterprise,
        isFree,
        paidUpUntil: isEnterprise ? null : cycleEndDate?.toISOString() || null,
      },
      features,
      billingContact: {
        email: data.billing_contact_email,
        supportUrl: data.enterprise_support_url,
      },
      createdAt: data.created_at,
      updatedAt: credits?.updated_at || data.created_at,
    };
  }

  /**
   * Gets plan details and feature access for an organization.
   * @param orgName
   * @returns Promise<PlanDetails>
   */
  async getPlanDetails(args: Partial<{ orgName: string }>) {
    const subscriptionStatus = await this.getSubscriptionStatus(args);

    return {
      planName: subscriptionStatus.planName,
      tier: subscriptionStatus.tier,
      features: subscriptionStatus.features,
      limits: {
        maxCreditsPerCycle: subscriptionStatus.maxCreditsPerCycle,
        refillCycleDays: subscriptionStatus.billingCycle.cycleDays,
        pricePerCredit: subscriptionStatus.features.pricePerCredit,
      },
    };
  }

  /**
   * Gets the credit transaction history for an organization.
   * @param orgName - The unique organization name
   * @param args - Optional parameters for pagination and filtering
   * @returns Promise<Array> - Array of organization credit transactions
   */
  async getOrganizationCreditTransactions(
    args: Partial<{
      orgName: string;
      limit: number;
      offset: number;
      transactionType?: string;
    }> = {},
  ) {
    const orgName = ensure(
      args.orgName,
      "orgName is required to get organization credit transactions",
    );
    console.log(
      "getOrganizationCreditTransactions for orgName=",
      orgName,
      args,
    );
    const { limit = 50, offset = 0, transactionType } = args;

    let query = this.supabaseClient
      .from("organization_credit_transactions")
      .select("*, organizations!inner(org_name)")
      .eq("organizations.org_name", orgName)
      .order("created_at", { ascending: false })
      .range(offset, offset + limit - 1);

    if (transactionType) {
      query = query.eq("transaction_type", transactionType);
    }

    const { data, error } = await query;

    if (error) {
      throw error;
    } else if (!data) {
      throw new MissingDataError(
        `Unable to find credit transactions for organization orgName=${orgName}`,
      );
    }
    return data;
  }

  /**
   * Gets the dynamic connector client for the current organization.
   * @param orgName
   */
  async getConnectors(
    args: Partial<{ orgName: string }>,
  ): Promise<Tables<"dynamic_connectors">[]> {
    const orgName = ensure(args.orgName, "orgName is required");

    const { data, error } = await this.supabaseClient
      .from("dynamic_connectors")
      .select("*,organizations!inner(org_name)")
      .eq("organizations.org_name", orgName)
      .is("deleted_at", null);

    if (error) {
      throw error;
    }

    return data;
  }

  /**
   * Gets a specific dynamic connector by ID.
   * @param args - Contains the connector ID
   * @returns Promise<DynamicConnectorsRow> - The connector data
   */
  async getConnectorById(
    args: Partial<{ id: string }>,
  ): Promise<DynamicConnectorsRow> {
    const id = ensure(args.id, "id is required");

    const { data, error } = await this.supabaseClient
      .from("dynamic_connectors")
      .select("*")
      .eq("id", id)
      .is("deleted_at", null)
      .single();

    if (error) {
      throw error;
    } else if (!data) {
      throw new MissingDataError(`Unable to find connector with id=${id}`);
    }

    return data;
  }

  /**
   * Creates a new dynamic connector.
   * @param args - Contains data for the new connector and credentials
   * @returns Promise<Tables<"dynamic_connectors">> - The created connector
   */
  async createConnector(
    args: Partial<{
      data: DynamicConnectorsInsert;
      credentials: Record<string, string>;
    }>,
  ): Promise<Tables<"dynamic_connectors">> {
    const data = dynamicConnectorsInsertSchema.parse(args.data);
    const credentials = ensure(args.credentials, "credentials are required");

    const customHeaders = await this.createSupabaseAuthHeaders();

    const response = await fetch("/api/v1/connector", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...customHeaders,
      },
      body: JSON.stringify({
        data,
        credentials,
      }),
    });

    const json = await response.json();

    if (!response.ok) {
      throw new Error("Error creating connector: " + json.error);
    }

    return dynamicConnectorsRowSchema.parse(json);
  }

  /**
   * Deletes a dynamic connector by its ID.
   * @param args - Contains the ID of the connector to delete
   * @returns Promise<void>
   */
  async deleteConnector(args: Partial<{ id: string }>): Promise<void> {
    const id = ensure(
      args.id,
      "id is required for deleting a dynamic connector",
    );

    const customHeaders = await this.createSupabaseAuthHeaders();
    const searchParams = new URLSearchParams({ id });

    const response = await fetch(
      `/api/v1/connector?${searchParams.toString()}`,
      {
        method: "DELETE",
        headers: {
          "Content-Type": "application/json",
          ...customHeaders,
        },
      },
    );

    const json = await response.json();

    if (!response.ok) {
      throw new Error("Error deleting connector: " + json.error);
    }
  }

  /**
   * Syncs a dynamic connector to refresh its schema and metadata.
   * @param id
   */
  async syncConnector(args: Partial<{ id: string }>): Promise<void> {
    const id = ensure(args.id, "id is required to sync connector");

    const customHeaders = await this.createSupabaseAuthHeaders();
    const searchParams = new URLSearchParams({ id });

    const response = await fetch(
      `/api/v1/connector/sync?${searchParams.toString()}`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...customHeaders,
        },
      },
    );

    if (!response.ok) {
      const error = await response.json();
      throw new Error(`Error syncing connector: ${error.error}`);
    }

    return;
  }

  /**
   * Gets dynamic connectors and contextual information.
   * @param orgName
   * @returns Promise<{ table: DynamicTableContextsRow; columns: DynamicColumnContextsRow[] }>
   * - Returns the tables context and an array of column contexts for the connector
   */
  async getDynamicConnectorAndContextsByOrgId(args: {
    orgName: string;
  }): Promise<
    {
      connector: DynamicConnectorsRow;
      contexts: {
        table: DynamicTableContextsRow;
        columns: DynamicColumnContextsRow[];
      }[];
    }[]
  > {
    const orgName = ensure(args.orgName, "orgName is required to get contexts");

    const { data, error } = await this.supabaseClient
      .from("dynamic_connectors")
      .select(
        "*, organizations!inner(org_name), dynamic_table_contexts(*, dynamic_column_contexts(*))",
      )
      .eq("organizations.org_name", orgName);

    if (error) {
      throw error;
    } else if (!data) {
      throw new MissingDataError(
        `Unable to find connectors for orgName=${orgName}`,
      );
    }

    return data.map((dynamicConnector) => {
      const { dynamic_table_contexts: _, ...unparsedConnector } =
        dynamicConnector;
      const connector = dynamicConnectorsRowSchema.parse(unparsedConnector);
      const contexts = dynamicConnector.dynamic_table_contexts.map(
        (tableContext) => {
          const { dynamic_column_contexts: columns, ...table } = tableContext;
          return {
            table: dynamicTableContextsRowSchema.parse(table),
            columns: columns.map((c) =>
              dynamicColumnContextsRowSchema.parse(c),
            ),
          };
        },
      );
      return { connector, contexts };
    });
  }

  /**
   * Gets contextual information for a dynamic connector's tables and columns.
   * @param id
   * @returns Promise<{ table: DynamicTableContextsRow; columns: DynamicColumnContextsRow[] }>
   * - Returns the tables context and an array of column contexts for the connector
   */
  async getDynamicConnectorContexts(args: { id: string }): Promise<
    {
      table: DynamicTableContextsRow;
      columns: DynamicColumnContextsRow[];
    }[]
  > {
    const id = ensure(args.id, "id is required to get contexts");

    const { data, error } = await this.supabaseClient
      .from("dynamic_table_contexts")
      .select("*, dynamic_column_contexts(*)")
      .eq("connector_id", id);

    if (error) {
      throw error;
    } else if (!data) {
      throw new MissingDataError(
        `Unable to find contexts for connector id=${id}`,
      );
    }
    return data.map((row) => {
      const { dynamic_column_contexts: columns, ...table } = row;
      return { table, columns };
    });
  }

  /**
   * Upserts dynamic connector contexts for a given connector.
   * - This will insert or update the table and column contexts
   * @param args - Contains the table and columns data to upsert
   */
  async upsertDynamicConnectorContexts(
    args: Partial<{
      table: DynamicTableContextsRow | null;
      columns: DynamicColumnContextsRow[] | null;
    }>,
  ) {
    const table = args.table
      ? dynamicTableContextsRowSchema.parse(args.table)
      : null;
    const columns = args.columns
      ? args.columns.map((col) => {
          return dynamicColumnContextsRowSchema.parse(col);
        })
      : null;
    if (table) {
      const { error: tableError } = await this.supabaseClient
        .from("dynamic_table_contexts")
        .upsert(table);
      if (tableError) {
        throw tableError;
      }
    }
    if (columns && columns.length > 0) {
      const { error: columnsError } = await this.supabaseClient
        .from("dynamic_column_contexts")
        .upsert(columns);
      if (columnsError) {
        throw columnsError;
      }
    }
  }

  /**
   * Gets connector relationships for an organization.
   * @param orgName
   */
  async getConnectorRelationships(args: {
    orgName: string;
  }): Promise<ConnectorRelationshipsRow[]> {
    const orgName = ensure(
      args.orgName,
      "orgName is required to get relationships",
    );

    const { data, error } = await this.supabaseClient
      .from("connector_relationships")
      .select("*, organizations!inner(org_name)")
      .eq("organizations.org_name", orgName);

    if (error) {
      throw error;
    } else if (!data) {
      throw new MissingDataError(
        `Unable to find connector relationships for orgName=${orgName}`,
      );
    }

    return data;
  }

  /**
   * Creates a new connector relationship.
   * @param args
   */
  async createConnectorRelationship(
    args: Partial<{
      data: ConnectorRelationshipsInsert;
    }>,
  ): Promise<ConnectorRelationshipsRow> {
    const data = connectorRelationshipsInsertSchema.parse(args.data);

    // For OSO default entities, we store it in the target_oso_entity field,
    // e.g: artifact_id, project_id, etc.
    if (data.target_table_id === DEFAULT_OSO_TABLE_ID) {
      data.target_oso_entity = data.target_column_name;
      data.target_table_id = null;
      data.target_column_name = null;
    }

    assert(
      (data.source_table_id && data.source_column_name) ||
        data.target_oso_entity,
      "Either source_table_id and source_column_name or target_oso_entity must be provided",
    );

    assert(
      data.source_table_id !== data.target_table_id,
      "Source and target table IDs must be different",
    );

    const { data: relationshipData, error } = await this.supabaseClient
      .from("connector_relationships")
      .insert(data)
      .select()
      .single();

    if (error) {
      throw error;
    } else if (!relationshipData) {
      throw new MissingDataError("Failed to create connector relationship");
    }

    return relationshipData;
  }

  /**
   * Deletes a connector relationship by its ID.
   * @param args
   */
  async deleteConnectorRelationship(
    args: Partial<{ id: string }>,
  ): Promise<void> {
    const id = ensure(
      args.id,
      "id is required to delete connector relationship",
    );

    const { error } = await this.supabaseClient
      .from("connector_relationships")
      .delete()
      .eq("id", id);

    if (error) {
      throw error;
    }
  }

  /**
   * Initiates a Stripe checkout session to buy credits.
   * @param args - Contains the packageId to purchase and required orgId
   * @returns Promise<{ sessionId: string; url: string }> - Stripe checkout session info
   */
  async buyCredits(
    args: Partial<{
      packageId: string;
      orgId: string;
    }>,
  ): Promise<{ sessionId: string; url: string; publishableKey: string }> {
    console.log("buyCredits: ", args);
    const packageId = ensure(args.packageId, "Missing packageId argument");
    const orgId = ensure(args.orgId, "Missing orgId argument");

    const {
      data: { session },
    } = await this.supabaseClient.auth.getSession();
    if (!session) {
      throw new AuthError("No active session");
    }

    const body: { packageId: string; orgId: string } = { packageId, orgId };

    const response = await fetch("/api/v1/stripe/checkout", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${session.access_token}`,
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || "Failed to create checkout session");
    }

    const data = await response.json();
    return {
      sessionId: data.sessionId,
      url: data.url,
      publishableKey: data.publishableKey,
    };
  }

  /**
   * Gets available credit packages for purchase.
   * @returns Array of credit packages with pricing
   */
  async getCreditPackages() {
    console.log("getCreditPackages");
    return CREDIT_PACKAGES.map((pkg) => ({
      id: pkg.id,
      name: pkg.name,
      credits: pkg.credits,
      price: pkg.price,
      displayPrice: `$${(pkg.price / 100).toFixed(2)}`,
    }));
  }

  /**
   * Gets the user's purchase history.
   * @returns Promise<Array> - Array of purchase intents
   */
  async getMyPurchaseHistory() {
    console.log("getMyPurchaseHistory");
    const user = await this.getUser();
    const { data, error } = await this.supabaseClient
      .from("purchase_intents")
      .select("*")
      .eq("user_id", user.id)
      .order("created_at", { ascending: false });

    if (error) {
      throw error;
    }
    return data || [];
  }

  /**
   * Creates an invitation to join an organization
   * @param args - Contains the organization name and email (invitees are always assigned 'member' role)
   * @returns Promise<any> - The created invitation
   */
  async createInvitation(
    args: Partial<{
      orgName: string;
      email: string;
    }>,
  ) {
    console.log("createInvitation: ", args);
    const orgName = ensure(args.orgName, "Missing orgName argument");
    const email = ensure(args.email, "Missing email argument");

    const response = await fetch("/api/v1/invitations/create", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        orgName,
        email,
      }),
    });

    const result = await response.json();

    if (!response.ok) {
      throw new Error(result.error || "Failed to create invitation");
    }

    return result.invitation;
  }

  /**
   * Lists all invitations for an organization
   * @param args - Contains the organization name
   * @returns Promise<any[]> - Array of invitations
   */
  async listInvitationsForOrg(
    args: Partial<{
      orgName: string;
    }>,
  ) {
    console.log("listInvitationsForOrg: ", args);
    const orgName = ensure(args.orgName, "Missing orgName argument");

    const { data, error } = await this.supabaseClient
      .from("invitations")
      .select(
        `
        *,
        inviter:user_profiles!invited_by(id, email, full_name),
        organizations!inner(org_name)
      `,
      )
      .eq("organizations.org_name", orgName)
      .is("deleted_at", null)
      .gt("expires_at", new Date().toISOString())
      .order("created_at", { ascending: false });

    if (error) {
      throw error;
    }

    return data || [];
  }

  /**
   * Accepts an invitation using the invitation ID
   * @param args - Contains the invitation ID
   * @returns Promise<boolean> - Success status
   */
  async acceptInvitation(
    args: Partial<{
      invitationId: string;
    }>,
  ) {
    console.log("acceptInvitation: ", args);
    const invitationId = ensure(
      args.invitationId,
      "Missing invitationId argument",
    );

    const user = await this.getUser();

    const { data, error } = await this.supabaseClient.rpc("accept_invitation", {
      p_invitation_id: invitationId,
      p_user_id: user.id,
    });

    if (error) {
      throw error;
    }

    return data;
  }

  /**
   * Gets an invitation by its ID
   * @param args - Contains the invitation id
   * @returns Promise<object> - The invitation details
   */
  async getInviteById(
    args: Partial<{
      inviteId: string;
    }>,
  ) {
    console.log("getInviteById: ", args);
    const inviteId = ensure(args.inviteId, "Missing inviteId argument");

    const { data, error } = await this.supabaseClient
      .from("invitations")
      .select(
        `*, inviter:user_profiles!invited_by(email), organizations!inner(org_name)`,
      )
      .eq("id", inviteId)
      .is("deleted_at", null)
      .single();

    if (error) {
      throw error;
    } else if (!data) {
      throw new MissingDataError(
        `Unable to find invitation with id=${inviteId}`,
      );
    }

    return {
      invite_id: data.id,
      inviter_email: data.inviter?.email,
      invitee_email: data.email,
      org_id: data.org_id,
      org_name: data.organizations?.org_name,
      expires_at: data.expires_at,
      created_at: data.created_at,
    };
  }

  /**
   * Deletes/revokes an invitation, only by the user who created it
   * @param args - Contains the invitation id
   * @returns Promise<boolean> - Returns true if revoked, false if invitation not found or not pending
   */
  async deleteInvitation(
    args: Partial<{
      invitationId: string;
    }>,
  ) {
    console.log("deleteInvitation: ", args);
    const invitationId = ensure(
      args.invitationId,
      "Missing invitationId argument",
    );

    const { error } = await this.supabaseClient
      .from("invitations")
      .update({
        deleted_at: new Date().toISOString(),
      })
      .eq("id", invitationId);

    if (error) {
      throw error;
    }

    return true;
  }

  /**
   * Checks if the current user has permission to access a resource
   * @param resourceType
   * @param resourceId
   */
  async checkResourcePermission(
    args: Partial<{
      resourceType: "notebook" | "chat";
      resourceId: string;
    }>,
  ): Promise<ResourcePermissionResponse> {
    const { resourceType, resourceId } = {
      resourceType: ensure(args.resourceType, "Missing resourceType argument"),
      resourceId: ensure(args.resourceId, "Missing resourceId argument"),
    };

    const { data, error } = await this.supabaseClient.rpc(
      "check_resource_permission",
      {
        p_resource_type: resourceType,
        p_resource_id: resourceId,
      },
    );

    if (error || !data) {
      console.log("Error checking resource permission:", error);
      return {
        hasAccess: false,
        permissionLevel: "none",
        resourceId: "unknown",
      };
    }

    return resourcePermissionResponseSchema.parse(data);
  }

  /**
   * Grants permission to a user on a resource
   * @param resourceType
   * @param resourceId
   * @param targetUserId - null for public permissions, string for specific user
   * @param permissionLevel
   */
  async grantResourcePermission(
    args: Partial<{
      resourceType: "notebook" | "chat";
      resourceId: string;
      targetUserId?: string | null;
      permissionLevel: "read" | "write" | "admin" | "owner";
    }>,
  ) {
    const { resourceType, resourceId, permissionLevel } = {
      resourceType: ensure(args.resourceType, "Missing resourceType argument"),
      resourceId: ensure(args.resourceId, "Missing resourceId argument"),
      permissionLevel: ensure(
        args.permissionLevel,
        "Missing permissionLevel argument",
      ),
    };

    const targetUserId =
      "targetUserId" in args
        ? args.targetUserId
        : ensure(args.targetUserId, "Missing targetUserId argument");

    if (targetUserId === undefined) {
      throw new Error(
        "Please provide a targetUserId explicitly, use null for public permissions",
      );
    }

    const user = await this.getUser();
    const column = resourceType === "notebook" ? "notebook_id" : "chat_id";

    const targetDescription =
      targetUserId === null ? "public" : `user ${targetUserId}`;
    console.log(
      `Granting ${permissionLevel} permission on ${resourceType} ${resourceId} to ${targetDescription} by ${user.id}`,
    );

    const updateQuery = this.supabaseClient
      .from("resource_permissions")
      .update({
        permission_level: permissionLevel,
        granted_by: user.id,
        updated_at: new Date().toISOString(),
      });

    const finalUpdateQuery =
      targetUserId === null
        ? updateQuery.is("user_id", null)
        : updateQuery.eq("user_id", targetUserId);

    const { data: updateData } = await finalUpdateQuery
      .eq(column, resourceId)
      .is("revoked_at", null)
      .select()
      .throwOnError();

    if (updateData && updateData.length > 0) {
      console.log("Permission updated successfully:", updateData);
      return updateData;
    }

    const { data } = await this.supabaseClient
      .from("resource_permissions")
      .insert({
        user_id: targetUserId,
        permission_level: permissionLevel,
        granted_by: user.id,
        [column]: resourceId,
      })
      .select()
      .throwOnError();

    console.log("Permission granted successfully:", data);
    return data;
  }

  /**
   * Makes a resource public by granting permissions to everyone
   */
  async grantPublicPermission(
    args: Partial<{
      resourceType: "notebook" | "chat";
      resourceId: string;
      permissionLevel: "read" | "write" | "admin" | "owner";
    }>,
  ) {
    return this.grantResourcePermission({
      ...args,
      targetUserId: null,
    });
  }

  /**
   * Revokes permission from a user on a resource
   * @param resourceType
   * @param resourceId
   * @param targetUserId - null for public permissions, string for specific user
   */
  async revokeResourcePermission(
    args: Partial<{
      resourceType: "notebook" | "chat";
      resourceId: string;
      targetUserId?: string | null;
    }>,
  ) {
    const { resourceType, resourceId } = {
      resourceType: ensure(args.resourceType, "Missing resourceType argument"),
      resourceId: ensure(args.resourceId, "Missing resourceId argument"),
    };

    const targetUserId =
      "targetUserId" in args
        ? args.targetUserId
        : ensure(args.targetUserId, "Missing targetUserId argument");

    if (targetUserId === undefined) {
      throw new Error(
        "Please provide a targetUserId explicitly, use null for public permissions",
      );
    }

    const column = resourceType === "notebook" ? "notebook_id" : "chat_id";

    const revokeQuery = this.supabaseClient
      .from("resource_permissions")
      .update({ revoked_at: new Date().toISOString() });

    const finalRevokeQuery =
      targetUserId === null
        ? revokeQuery.is("user_id", null)
        : revokeQuery.eq("user_id", targetUserId);

    await finalRevokeQuery.eq(column, resourceId).throwOnError();
  }

  /**
   * Makes a resource private by removing public access
   */
  async revokePublicPermission(
    args: Partial<{
      resourceType: "notebook" | "chat";
      resourceId: string;
    }>,
  ) {
    return this.revokeResourcePermission({
      ...args,
      targetUserId: null,
    });
  }

  /**
   * Lists all permissions for a resource
   * @param resourceType
   * @param resourceId
   */
  async listResourcePermissions(
    args: Partial<{
      resourceType: "notebook" | "chat";
      resourceId: string;
    }>,
  ) {
    const { resourceType, resourceId } = {
      resourceType: ensure(args.resourceType, "Missing resourceType argument"),
      resourceId: ensure(args.resourceId, "Missing resourceId argument"),
    };

    const column = resourceType === "notebook" ? "notebook_id" : "chat_id";

    const { data, error } = await this.supabaseClient
      .from("resource_permissions")
      .select(
        `
        *,
        user:user_profiles!user_id(id, email, full_name),
        granted_by_user:user_profiles!granted_by(id, email, full_name)
      `,
      )
      .eq(column, resourceId)
      .is("revoked_at", null);

    if (error) {
      throw error;
    }

    return data || [];
  }

  /**
   * Get list of all enterprise organizations with their credit balances
   * @returns Promise<Array>
   */
  async getEnterpriseOrganizations() {
    const { data } = await this.supabaseClient
      .from("organizations")
      .select(
        `
        id,
        org_name,
        created_at,
        pricing_plan!inner(plan_name, price_per_credit, max_credits_per_cycle, refill_cycle_days),
        organization_credits(credits_balance, last_refill_at, updated_at)
      `,
      )
      .eq("pricing_plan.plan_name", "ENTERPRISE")
      .is("deleted_at", null)
      .order("org_name")
      .throwOnError();

    return data || [];
  }

  /**
   * Get list of all organizations with their credit balances (admin only)
   * @returns Promise<Array>
   */
  async getAllOrganizationsWithCredits() {
    const { data } = await this.supabaseClient
      .from("organizations")
      .select(
        `
        id,
        org_name,
        created_at,
        pricing_plan!inner(plan_name, price_per_credit, max_credits_per_cycle, refill_cycle_days),
        organization_credits(credits_balance, last_refill_at, updated_at)
      `,
      )
      .is("deleted_at", null)
      .order("org_name")
      .throwOnError();

    return data || [];
  }

  /**
   * Creates an R2 bucket for an enterprise organization via API route
   * @param orgName - organization name
   * @returns Promise<void>
   */
  private async createEnterpriseOrgR2Bucket(orgName: string) {
    const customHeaders = await this.createSupabaseAuthHeaders();

    await fetch("/api/v1/organizations/create-bucket", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...customHeaders,
      },
      body: JSON.stringify({ orgName }),
    });
  }

  /**
   * Gets a pricing plan by name
   * @param planName - The name of the plan (e.g., "ENTERPRISE", "FREE", "PRO", "STARTER")
   * @returns Promise<{ plan_id: string; plan_name: string }> - The plan data
   */
  private async getPlanByName(planName: string) {
    const { data: plan } = await this.supabaseClient
      .from("pricing_plan")
      .select("plan_id, plan_name")
      .eq("plan_name", planName)
      .order("created_at", { ascending: false })
      .limit(1)
      .single()
      .throwOnError();

    if (!plan) {
      throw new Error(`Pricing plan not found: ${planName}`);
    }

    return plan;
  }

  /**
   * Promote an existing organization to enterprise tier
   * @param orgName
   * @returns Promise<boolean>
   */
  async promoteOrganizationToEnterprise(args: Partial<{ orgName: string }>) {
    const orgName = ensure(
      args.orgName,
      "orgName is required to promote organization to enterprise",
    );

    const enterprisePlan = await this.getPlanByName("ENTERPRISE");

    await this.supabaseClient
      .from("organizations")
      .update({ plan_id: enterprisePlan.plan_id })
      .eq("org_name", orgName)
      .throwOnError();

    const hasFetch = typeof fetch === "function";
    if (hasFetch) {
      await this.createEnterpriseOrgR2Bucket(orgName);
    }

    return true;
  }

  /**
   * Demote an organization from enterprise tier to free tier
   * @param orgName
   * @returns Promise<boolean>
   */
  async demoteOrganizationFromEnterprise(args: Partial<{ orgName: string }>) {
    const orgName = ensure(
      args.orgName,
      "orgName is required to demote organization from enterprise",
    );

    const freePlan = await this.getPlanByName("FREE");

    await this.supabaseClient
      .from("organizations")
      .update({ plan_id: freePlan.plan_id })
      .eq("org_name", orgName)
      .throwOnError();

    return true;
  }

  /**
   * Update an organization's tier to any available plan
   * @param orgName - The organization name
   * @param tier - The tier name (e.g., "FREE", "STARTER", "PRO", "ENTERPRISE")
   * @returns Promise<boolean>
   */
  async updateOrganizationTier(
    args: Partial<{ orgName: string; tier: string }>,
  ) {
    const orgName = ensure(
      args.orgName,
      "orgName is required to update organization tier",
    );
    const tier = ensure(
      args.tier,
      "tier is required to update organization tier",
    );

    const { data: org } = await this.supabaseClient
      .from("organizations")
      .select("pricing_plan(plan_name)")
      .eq("org_name", orgName)
      .is("deleted_at", null)
      .single()
      .throwOnError();

    if (!org) {
      throw new MissingDataError(`Organization not found: ${orgName}`);
    }

    if (!org.pricing_plan) {
      throw new MissingDataError(
        `Pricing plan not found for organization: ${orgName}`,
      );
    }

    const currentPlanName = org.pricing_plan.plan_name;

    if (currentPlanName === tier) {
      console.log(
        `Organization ${orgName} is already on the ${tier} tier. No changes made.`,
      );
      return true;
    }

    const targetPlan = await this.getPlanByName(tier);

    await this.supabaseClient
      .from("organizations")
      .update({ plan_id: targetPlan.plan_id })
      .eq("org_name", orgName)
      .throwOnError();

    if (tier === "ENTERPRISE") {
      const hasFetch = typeof fetch === "function";
      if (hasFetch) {
        await this.createEnterpriseOrgR2Bucket(orgName);
      }
    }

    return true;
  }

  /**
   * Manually add credits to organization balance
   * @param args
   * @returns Promise<boolean>
   */
  async addOrganizationCredits(
    args: Partial<{
      orgName: string;
      amount: number;
      reason?: string;
    }>,
  ) {
    const orgName = ensure(
      args.orgName,
      "orgName is required to add organization credits",
    );
    const { amount, reason } = args;

    if (!amount || amount <= 0) {
      throw new Error("Amount must be a positive number");
    }

    const org = await this.getOrganizationByName({ orgName });
    const user = await this.getUser();

    const { data: currentCredits } = await this.supabaseClient
      .from("organization_credits")
      .select("credits_balance")
      .eq("org_id", org.id)
      .maybeSingle()
      .throwOnError();

    const currentBalance = currentCredits?.credits_balance || 0;
    const newBalance = currentBalance + amount;

    await this.supabaseClient
      .from("organization_credits")
      .upsert(
        {
          org_id: org.id,
          credits_balance: newBalance,
          last_refill_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
        { onConflict: "org_id" },
      )
      .throwOnError();

    await this.supabaseClient
      .from("organization_credit_transactions")
      .insert({
        org_id: org.id,
        user_id: user.id,
        amount: amount,
        transaction_type: "admin_grant",
        metadata: {
          reason: reason || "Manual admin credit addition",
          admin_action: true,
          previous_balance: currentBalance,
          new_balance: newBalance,
        },
        created_at: new Date().toISOString(),
      })
      .throwOnError();

    return true;
  }

  /**
   * Manually set organization's credits to an exact amount
   * @param args
   * @return Promise<boolean>
   */
  async setOrganizationCredits(
    args: Partial<{
      orgName: string;
      amount: number;
      reason?: string;
    }>,
  ) {
    const orgName = ensure(
      args.orgName,
      "orgName is required to set organization credits",
    );
    const { amount, reason } = args;

    if (amount === undefined || amount < 0) {
      throw new Error("Amount must be a non-negative number");
    }

    const org = await this.getOrganizationByName({ orgName });
    const user = await this.getUser();

    const currentBalance = await this.getOrganizationCredits({
      orgName,
    });

    const newBalance = amount;

    await this.supabaseClient
      .from("organization_credits")
      .upsert(
        {
          org_id: org.id,
          credits_balance: newBalance,
          updated_at: new Date().toISOString(),
        },
        { onConflict: "org_id" },
      )
      .throwOnError();

    await this.supabaseClient
      .from("organization_credit_transactions")
      .insert({
        org_id: org.id,
        user_id: user.id,
        amount: newBalance - currentBalance,
        transaction_type: "admin_set",
        metadata: {
          reason: reason || "Manual admin credit set",
          admin_action: true,
          previous_balance: currentBalance,
          new_balance: newBalance,
        },
        created_at: new Date().toISOString(),
      })
      .throwOnError();

    return true;
  }

  /**
   * Manually deduct credits from organization balance
   * @param args
   * @returns Promise<boolean>
   */
  async deductOrganizationCredits(
    args: Partial<{
      orgName: string;
      amount: number;
      reason?: string;
    }>,
  ) {
    const orgName = ensure(
      args.orgName,
      "orgName is required to deduct organization credits",
    );
    const { amount, reason } = args;

    if (!amount || amount <= 0) {
      throw new Error("Amount must be a positive number");
    }

    const org = await this.getOrganizationByName({ orgName });
    const user = await this.getUser();

    const { data: currentCredits } = await this.supabaseClient
      .from("organization_credits")
      .select("credits_balance")
      .eq("org_id", org.id)
      .single()
      .throwOnError();

    const currentBalance = currentCredits.credits_balance;

    if (currentBalance < amount) {
      throw new Error("Insufficient credits balance");
    }

    const newBalance = currentBalance - amount;

    await this.supabaseClient
      .from("organization_credits")
      .update({
        credits_balance: newBalance,
        updated_at: new Date().toISOString(),
      })
      .eq("org_id", org.id)
      .throwOnError();

    await this.supabaseClient
      .from("organization_credit_transactions")
      .insert({
        org_id: org.id,
        user_id: user.id,
        amount: -amount,
        transaction_type: "admin_deduct",
        metadata: {
          reason: reason || "Manual admin credit deduction",
          admin_action: true,
          previous_balance: currentBalance,
          new_balance: newBalance,
        },
        created_at: new Date().toISOString(),
      })
      .throwOnError();

    return true;
  }

  /**
   * Get a Supabase realtime channel.
   * @param channelName The name of the channel. Currently formatted as `<room_type>:<room_id>`.
   * e.g: `notebook:notebook-id`
   * @returns The Supabase realtime channel.
   */
  async getRealtimeChannel(channelName: string) {
    const user = await this.getUser();
    return this.supabaseClient.channel(channelName, {
      config: {
        private: true,
        presence: {
          key: user.id,
        },
      },
    });
  }

  async saveNotebookPreview(
    args: Partial<{
      notebookId: string;
      base64Image: string;
    }>,
  ) {
    const notebookId = ensure(args.notebookId, "Missing notebookId argument");
    const base64Image = ensure(
      args.base64Image,
      "Missing base64Image argument",
    );

    const SAVE_NOTEBOOK_PREVIEW_MUTATION = gql(`
      mutation SavePreview($input: SaveNotebookPreviewInput!) {
        saveNotebookPreview(input: $input) {
          success
          message
        }
      }
    `);

    logger.log(
      `Uploading notebook preview for ${notebookId}. Image size: ${base64Image.length} bytes`,
    );

    const response = await fetch("/api/v1/osograph", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        query: print(SAVE_NOTEBOOK_PREVIEW_MUTATION),
        variables: {
          input: {
            notebookId,
            preview: base64Image,
          },
        },
      }),
    });

    const result = await response.json();

    if (result.errors) {
      logger.error("Failed to save preview:", result.errors[0].message);
      throw new Error(`Failed to save preview: ${result.errors[0].message}`);
    }

    const payload = result.data?.saveNotebookPreview;
    if (!payload) {
      throw new Error("No response data from preview save mutation");
    }

    if (payload.success) {
      logger.log(
        `Successfully saved notebook preview for ${notebookId} to bucket "notebook-previews"`,
      );
      logger.info("Notebook preview saved successfully");
    }

    return payload;
  }

  private async createSupabaseAuthHeaders() {
    const { data: sessionData, error } =
      await this.supabaseClient.auth.getSession();
    if (error) {
      throw error;
    } else if (!sessionData.session) {
      throw new AuthError("Not logged in");
    }

    return {
      Authorization: `Bearer ${sessionData.session.access_token}`,
      "X-Supabase-Auth": `${sessionData.session.access_token}:${sessionData.session.refresh_token}`,
    };
  }

  async createDataset(
    args: Partial<{
      orgId: string;
      name: string;
      displayName: string;
      description: string;
      datasetType: DatasetType;
      isPublic: boolean;
    }>,
  ) {
    const { orgId, name, displayName, description, datasetType, isPublic } = {
      orgId: ensure(args.orgId, "Missing orgId argument"),
      name: ensure(args.name, "Missing name argument"),
      displayName: ensure(args.displayName, "Missing displayName argument"),
      description: args.description,
      datasetType: ensure(args.datasetType, "Missing datasetType argument"),
      isPublic: args.isPublic,
    };

    const CREATE_DATASET_MUTATION = gql(`
      mutation CreateDataset($input: CreateDatasetInput!) {
        createDataset(input: $input) {
          success
          message
          dataset {
            id
            name
            displayName
            description
            type
            isPublic
          }
        }
      }
    `);

    const response = await fetch("/api/v1/osograph", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        query: print(CREATE_DATASET_MUTATION),
        variables: {
          input: {
            orgId,
            name,
            displayName,
            description,
            type: datasetType,
            isPublic,
          },
        },
      }),
    });

    const result = await response.json();

    if (result.errors) {
      logger.error("Failed to create dataset:", result.errors[0].message);
      throw new Error(`Failed to create dataset: ${result.errors[0].message}`);
    }

    const payload = result.data?.createDataset;
    if (!payload) {
      throw new Error("No response data from create dataset mutation");
    }

    if (payload.success) {
      logger.log(`Successfully created dataset "${displayName}"`);
    }

    return payload.dataset;
  }

  async updateDataset(
    args: Partial<{
      datasetId: string;
      name: string;
      displayName: string;
      description: string;
      isPublic: boolean;
    }>,
  ) {
    const { datasetId, name, displayName, description, isPublic } = {
      datasetId: ensure(args.datasetId, "Missing datasetId argument"),
      name: args.name,
      displayName: args.displayName,
      description: args.description,
      isPublic: args.isPublic,
    };

    const UPDATE_DATASET_MUTATION = gql(`
      mutation UpdateDataset($input: UpdateDatasetInput!) {
        updateDataset(input: $input) {
          success
          message
          dataset {
            id
            name
            displayName
            description
            isPublic
          }
        }
      }
    `);

    const response = await fetch("/api/v1/osograph", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        query: print(UPDATE_DATASET_MUTATION),
        variables: {
          input: {
            id: datasetId,
            name,
            displayName,
            description,
            isPublic,
          },
        },
      }),
    });

    const result = await response.json();

    if (result.errors) {
      logger.error("Failed to update dataset:", result.errors[0].message);
      throw new Error(`Failed to update dataset: ${result.errors[0].message}`);
    }

    const payload = result.data?.updateDataset;
    if (!payload) {
      throw new Error("No response data from update dataset mutation");
    }

    if (payload.success) {
      logger.log(`Successfully updated dataset "${displayName}"`);
    }

    return payload.dataset;
  }

  async createDataModel(
    args: Partial<{
      orgId: string;
      datasetId: string;
      name: string;
      isEnabled: boolean;
    }>,
  ) {
    const { orgId, datasetId, name, isEnabled } = {
      orgId: ensure(args.orgId, "Missing orgId argument"),
      datasetId: ensure(args.datasetId, "Missing datasetId argument"),
      name: ensure(args.name, "Missing name argument"),
      isEnabled: args.isEnabled ?? false,
    };

    const CREATE_DATA_MODEL_MUTATION = gql(`
      mutation CreateDataModel($input: CreateDataModelInput!) {
        createDataModel(input: $input) {
          success
          message
          dataModel {
            id
            name
            isEnabled
          }
        }
      }
    `);

    const response = await fetch("/api/v1/osograph", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        query: print(CREATE_DATA_MODEL_MUTATION),
        variables: {
          input: {
            orgId,
            datasetId,
            name,
            isEnabled,
          },
        },
      }),
    });

    const result = await response.json();

    if (result.errors) {
      logger.error("Failed to create dataModel:", result.errors[0].message);
      throw new Error(
        `Failed to create dataModel: ${result.errors[0].message}`,
      );
    }

    const payload = result.data?.createDataModel;
    if (!payload) {
      throw new Error("No response data from create dataModel mutation");
    }

    if (payload.success) {
      logger.log(`Successfully created dataModel "${name}"`);
    }

    return payload.dataModel;
  }

  async updateDataModel(
    args: Partial<{
      dataModelId: string;
      name?: string;
      isEnabled?: boolean;
    }>,
  ) {
    const { dataModelId, name, isEnabled } = {
      dataModelId: ensure(args.dataModelId, "Missing dataModelId argument"),
      name: args.name,
      isEnabled: args.isEnabled ?? false,
    };

    const UPDATE_DATA_MODEL_MUTATION = gql(`
      mutation UpdateDataModel($input: UpdateDataModelInput!) {
        updateDataModel(input: $input) {
          success
          message
          dataModel {
            id
            name
            isEnabled
          }
        }
      }
    `);

    const response = await fetch("/api/v1/osograph", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        query: print(UPDATE_DATA_MODEL_MUTATION),
        variables: {
          input: {
            dataModelId,
            name,
            isEnabled,
          },
        },
      }),
    });

    const result = await response.json();

    if (result.errors) {
      logger.error("Failed to update dataModel:", result.errors[0].message);
      throw new Error(
        `Failed to update dataModel: ${result.errors[0].message}`,
      );
    }

    const payload = result.data?.updateDataModel;
    if (!payload) {
      throw new Error("No response data from update dataModel mutation");
    }

    if (payload.success) {
      logger.log(`Successfully updated dataModel "${name}"`);
    }

    return payload.dataModel;
  }

  async createDataModelRevision(
    args: Partial<{
      dataModelId: string;
      name: string;
      displayName: string;
      description: string;
      language: string;
      code: string;
      cron: string;
      start: string;
      end: string;
      schema: any[];
      dependsOn: any[];
      partitionedBy: string[];
      clusteredBy: string[];
      kind: string;
      kindOptions: any;
    }>,
  ) {
    ensure(args.dataModelId, "Missing dataModelId argument");
    ensure(args.name, "Missing name argument");
    ensure(args.displayName, "Missing displayName argument");
    ensure(args.language, "Missing language argument");
    ensure(args.code, "Missing code argument");
    ensure(args.cron, "Missing cron argument");
    ensure(args.schema, "Missing schema argument");
    ensure(args.kind, "Missing kind argument");

    const CREATE_DATA_MODEL_REVISION_MUTATION = gql(`
      mutation CreateDataModelRevision($input: CreateDataModelRevisionInput!) {
        createDataModelRevision(input: $input) {
          success
          message
          dataModelRevision {
            id
            revisionNumber
          }
        }
      }
    `);

    const response = await fetch("/api/v1/osograph", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        query: print(CREATE_DATA_MODEL_REVISION_MUTATION),
        variables: {
          input: args,
        },
      }),
    });

    const result = await response.json();

    if (result.errors) {
      logger.error(
        "Failed to create dataModel revision:",
        result.errors[0].message,
      );
      throw new Error(
        `Failed to create dataModel revision: ${result.errors[0].message}`,
      );
    }

    const payload = result.data?.createDataModelRevision;
    if (!payload) {
      throw new Error(
        "No response data from create dataModel revision mutation",
      );
    }

    if (payload.success) {
      logger.log(
        `Successfully created dataModel revision for dataModel "${args.dataModelId}"`,
      );
    }

    return payload.dataModelRevision;
  }

  async createDataModelRelease(
    args: Partial<{
      dataModelId: string;
      dataModelRevisionId: string;
      description: string;
    }>,
  ) {
    const CREATE_DATA_MODEL_RELEASE_MUTATION = gql(`
      mutation CreateDataModelRelease($input: CreateDataModelReleaseInput!) {
        createDataModelRelease(input: $input) {
          success
          message
          dataModelRelease {
            id
          }
        }
      }
    `);

    const response = await fetch("/api/v1/osograph", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        query: print(CREATE_DATA_MODEL_RELEASE_MUTATION),
        variables: {
          input: args,
        },
      }),
    });

    const result = await response.json();

    if (result.errors) {
      logger.error(
        "Failed to create dataModel release:",
        result.errors[0].message,
      );
      throw new Error(
        `Failed to create dataModel release: ${result.errors[0].message}`,
      );
    }

    const payload = result.data?.createDataModelRelease;
    if (!payload) {
      throw new Error(
        "No response data from create dataModel release mutation",
      );
    }

    if (payload.success) {
      logger.log(
        `Successfully created dataModel release for dataModel "${args.dataModelId}"`,
      );
    }

    return payload.dataModelRelease;
  }

  async createStaticModel(
    args: Partial<{
      orgId: string;
      datasetId: string;
      name: string;
    }>,
  ) {
    const { orgId, datasetId, name } = {
      orgId: ensure(args.orgId, "Missing orgId argument"),
      datasetId: ensure(args.datasetId, "Missing datasetId argument"),
      name: ensure(args.name, "Missing name argument"),
    };

    const CREATE_STATIC_MODEL_MUTATION = gql(`
      mutation CreateStaticModel($input: CreateStaticModelInput!) {
        createStaticModel(input: $input) {
          success
          message
          staticModel {
            id
            name
          }
        }
      }
    `);

    const response = await fetch("/api/v1/osograph", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        query: print(CREATE_STATIC_MODEL_MUTATION),
        variables: {
          input: {
            orgId,
            datasetId,
            name,
          },
        },
      }),
    });

    const result = await response.json();

    if (result.errors) {
      logger.error("Failed to create staticModel:", result.errors[0].message);
      throw new Error(
        `Failed to create staticModel: ${result.errors[0].message}`,
      );
    }

    const payload = result.data?.createStaticModel;
    if (!payload) {
      throw new Error("No response data from create staticModel mutation");
    }

    if (payload.success) {
      logger.log(`Successfully created staticModel "${name}"`);
    }

    return payload.staticModel;
  }

  async updateStaticModel(
    args: Partial<{
      staticModelId: string;
      name?: string;
    }>,
  ) {
    const { staticModelId, name } = {
      staticModelId: ensure(
        args.staticModelId,
        "Missing staticModelId argument",
      ),
      name: args.name,
    };

    const UPDATE_STATIC_MODEL_MUTATION = gql(`
      mutation UpdateStaticModel($input: UpdateStaticModelInput!) {
        updateStaticModel(input: $input) {
          success
          message
          staticModel {
            id
            name
          }
        }
      }
    `);
    const response = await fetch("/api/v1/osograph", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        query: print(UPDATE_STATIC_MODEL_MUTATION),
        variables: {
          input: {
            staticModelId,
            name,
          },
        },
      }),
    });

    const result = await response.json();

    if (result.errors) {
      logger.error("Failed to update staticModel:", result.errors[0].message);
      throw new Error(
        `Failed to update staticModel: ${result.errors[0].message}`,
      );
    }

    const payload = result.data?.updateStaticModel;
    if (!payload) {
      throw new Error("No response data from update staticModel mutation");
    }

    if (payload.success) {
      logger.log(`Successfully updated staticModel "${name}"`);
    }

    return payload.staticModel;
  }

  async createUserModelRunRequest(
    args: Partial<{
      datasetId: string;
      selectedModels: string[];
    }>,
  ) {
    const datasetId = ensure(args.datasetId, "Missing datasetId argument");

    const CREATE_USER_MODEL_RUN_REQUEST_MUTATION = gql(`
      mutation CreateUserModelRunRequest($input: CreateUserModelRunRequestInput!) {
        createUserModelRunRequest(input: $input) {
          success
          message
          run {
            id
          }
        }
      }
    `);

    const response = await fetch("/api/v1/osograph", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        query: print(CREATE_USER_MODEL_RUN_REQUEST_MUTATION),
        variables: {
          input: {
            datasetId,
            selectedModels: args.selectedModels || [],
          },
        },
      }),
    });

    const result = await response.json();

    if (result.errors) {
      logger.error("Failed to create run request:", result.errors[0].message);
      throw new Error(
        `Failed to create run request: ${result.errors[0].message}`,
      );
    }

    const payload = result.data?.createUserModelRunRequest;
    if (!payload) {
      throw new Error("No response data from create run request mutation");
    }

    if (payload.success) {
      logger.log(
        `Successfully created Run request for user model dataset "${datasetId}"`,
      );
    }

    return payload.runRequest;
  }

  async createStaticModelRunRequest(
    args: Partial<{
      datasetId: string;
      selectedModels: string[];
    }>,
  ) {
    const datasetId = ensure(args.datasetId, "Missing datasetId argument");

    const CREATE_STATIC_MODEL_RUN_REQUEST_MUTATION = gql(`
      mutation CreateStaticModelRunRequest($input: CreateStaticModelRunRequestInput!) {
        createStaticModelRunRequest(input: $input) {
          success
          message
          run {
            id
          }
        }
      }
    `);

    const response = await fetch("/api/v1/osograph", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        query: print(CREATE_STATIC_MODEL_RUN_REQUEST_MUTATION),
        variables: {
          input: {
            datasetId,
            selectedModels: args.selectedModels || [],
          },
        },
      }),
    });

    const result = await response.json();

    if (result.errors) {
      logger.error("Failed to create run request:", result.errors[0].message);
      throw new Error(
        `Failed to create run request: ${result.errors[0].message}`,
      );
    }

    const payload = result.data?.createStaticModelRunRequest;
    if (!payload) {
      throw new Error("No response data from create run request mutation");
    }

    if (payload.success) {
      logger.log(
        `Successfully created Run request for static model dataset "${datasetId}"`,
      );
    }

    return payload.run;
  }
}

export { OsoAppClient };
