import _ from "lodash";
import { v4 as uuid4 } from "uuid";
import { SupabaseClient } from "@supabase/supabase-js";
import { assert, ensure } from "@opensource-observer/utils";
import { Database, Tables } from "@/lib/types/supabase";
import { MissingDataError, AuthError } from "@/lib/types/errors";
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
      throw new Error(`Error syncing connector: ${error.error}`);
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

    const { data: orgData, error: orgError } = await this.supabaseClient
      .from("organizations")
      .insert({
        org_name: orgName,
        created_by: user.id,
      })
      .select()
      .single();

    if (orgError) {
      throw orgError;
    }
    if (!orgData) {
      throw new MissingDataError("Failed to create organization");
    }

    const { error: memberError } = await this.supabaseClient
      .from("users_by_organization")
      .insert({
        org_id: orgData.id,
        user_id: user.id,
        user_role: "admin",
      });

    if (memberError) {
      throw memberError;
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
      .select("*")
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
    const { error } = await this.supabaseClient
      .from("users_by_organization")
      .update({ deleted_at: new Date().toISOString() })
      .eq("org_id", org.id)
      .eq("user_id", userId);
    if (error) {
      throw error;
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

  /**
   * Creates a new notebook
   * - Notebooks are stored under an organization
   * @param args
   * @returns
   */
  async createNotebook(args: Partial<NotebookKey>) {
    console.log("createNotebook: ", args);
    const orgName = ensure(args.orgName, "Missing orgName argument");
    const notebookName =
      args.notebookName || `notebook_${uuid4().substring(0, 5)}`;
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
      .select("*,organizations!inner(org_name)")
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
        organization:organizations!org_id(org_name)
      `,
      )
      .eq("organizations.org_name", orgName)
      .is("deleted_at", null)
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
        `
        id,
        email,
        org_id,
        status,
        expires_at,
        created_at,
        inviter:user_profiles!invited_by(email),
        organization:organizations!org_id(org_name)
      `,
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
      org_name: data.organization?.org_name,
      status: data.status,
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

    const user = await this.getUser();

    const { error } = await this.supabaseClient
      .from("invitations")
      .update({
        status: "revoked",
        updated_at: new Date().toISOString(),
      })
      .eq("id", invitationId)
      .eq("invited_by", user.id)
      .eq("status", "pending");

    if (error) {
      throw error;
    }

    return true;
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
}

export { OsoAppClient };
