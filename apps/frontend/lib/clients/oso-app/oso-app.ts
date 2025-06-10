import _ from "lodash";
import { SupabaseClient } from "@supabase/supabase-js";
import { ensure } from "@opensource-observer/utils";
import { Database, Tables } from "../../types/supabase";
import { MissingDataError, AuthError } from "../../types/errors";
import {
  dynamicConnectorsInsertSchema,
  dynamicConnectorsRowSchema,
} from "../../types/schema";
import type {
  DynamicColumnContextsRow,
  DynamicConnectorsInsert,
  DynamicConnectorsRow,
  DynamicTableContextsRow,
} from "../../types/schema-types";
import { CREDIT_PACKAGES } from "../stripe";

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
      orgId: string;
    }>,
  ) {
    console.log("createApiKey: ", args.name);
    const name = ensure(args.name, "Missing name argument");
    const apiKey = ensure(args.apiKey, "Missing apiKey argument");
    const orgId = ensure(args.orgId, "Missing orgId argument");
    const user = await this.getUser();
    const { error } = await this.supabaseClient.from("api_keys").insert({
      name,
      api_key: apiKey,
      user_id: user.id,
      org_id: orgId,
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

  async getApiKeysByOrgId(args: { orgId: string }) {
    const orgId = ensure(args.orgId, "Missing orgId argument");
    const { data, error } = await this.supabaseClient
      .from("api_keys")
      .select("id, name, user_id, created_at, org_id")
      .eq("org_id", orgId)
      .is("deleted_at", null);
    if (error) {
      throw error;
    } else if (!data) {
      throw new MissingDataError(`Unable to find API keys for org_id=${orgId}`);
    }
    return data;
  }

  /**
   * Removes an API Key
   * - We use `deleted_at` to mark the key as removed instead of deleting the row
   * @param orgId
   */
  async deleteApiKey(
    args: Partial<{
      keyId: string;
    }>,
  ) {
    console.log("deleteApiKey: ", args);
    const keyId = ensure(args.keyId, "Missing keyId argument");
    const { error } = await this.supabaseClient
      .from("api_keys")
      .update({ deleted_at: new Date().toISOString() })
      .eq("id", keyId);
    if (error) {
      throw error;
    }
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
   * Gets all users in an organization.
   * @param orgId
   * @returns
   */
  async getOrganizationMembers(
    args: Partial<{
      orgId: string;
    }>,
  ) {
    console.log("getOrganizationMembers: ", args);
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
      .in("id", _.keys(userRoleMap));
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
    console.log("addUserToOrganizationByEmail: ", args);
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
   * @param orgId
   * @param userId
   */
  async removeUserFromOrganization(
    args: Partial<{
      orgId: string;
      userId: string;
    }>,
  ) {
    console.log("removeUserFromOrganization: ", args);
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
    console.log("deleteOrganization: ", args);
    const orgId = ensure(args.orgId, "Missing orgId argument");
    const { error } = await this.supabaseClient
      .from("organizations")
      .update({ deleted_at: new Date().toISOString() })
      .eq("id", orgId);
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
  async createChat(args: Partial<{ orgId: string }>) {
    console.log("createChat: ", args);
    const orgId = ensure(args.orgId, "Missing orgId argument");
    const user = await this.getUser();

    const { data: chatData, error: chatError } = await this.supabaseClient
      .from("chat_history")
      .insert({
        org_id: orgId,
        display_name: new Date().toLocaleString(),
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

  async getChatsByOrgId(args: Partial<{ orgId: string }>) {
    console.log("getChatsByOrgId: ", args);
    const orgId = ensure(args.orgId, "Missing orgId argument");
    const { data, error } = await this.supabaseClient
      .from("chat_history")
      .select(
        "id,org_id,created_at,updated_at,deleted_at,created_by,display_name",
      )
      .eq("org_id", orgId)
      .is("deleted_at", null);
    if (error) {
      throw error;
    } else if (!data) {
      throw new MissingDataError(`Unable to find chats for orgId=${orgId}`);
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
  async deleteChat(args: Partial<{ chatId: string }>): Promise<void> {
    console.log("deleteChat: ", args);
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
   * Gets the current credit balance for the logged in user.
   * @returns Promise<number> - The current credit balance
   */
  async getMyCredits(): Promise<number> {
    console.log("getMyCredits");
    const user = await this.getUser();
    const { data, error } = await this.supabaseClient
      .from("user_credits")
      .select("credits_balance")
      .eq("user_id", user.id)
      .single();

    if (error) {
      throw error;
    } else if (!data) {
      throw new MissingDataError(
        `Unable to find credits for user id=${user.id}`,
      );
    }
    return data.credits_balance;
  }

  /**
   * Gets the credit transaction history for the logged in user.
   * @param args - Optional parameters for pagination and filtering
   * @returns Promise<Array> - Array of credit transactions
   */
  async getMyCreditTransactions(
    args: Partial<{
      limit: number;
      offset: number;
      transactionType?: string;
    }> = {},
  ) {
    console.log("getMyCreditTransactions: ", args);
    const user = await this.getUser();
    const { limit = 50, offset = 0, transactionType } = args;

    let query = this.supabaseClient
      .from("credit_transactions")
      .select("*")
      .eq("user_id", user.id)
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
        `Unable to find credit transactions for user id=${user.id}`,
      );
    }
    return data;
  }

  /**
   * Gets the dynamic connector client for the current organization.
   * @param orgId
   */
  async getConnectors(
    args: Partial<{ orgId: string }>,
  ): Promise<Tables<"dynamic_connectors">[]> {
    const orgId = ensure(args.orgId, "org_id is required");

    const { data, error } = await this.supabaseClient
      .from("dynamic_connectors")
      .select("*")
      .eq("org_id", orgId)
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
   * Initiates a Stripe checkout session to buy credits.
   * @param args - Contains the packageId to purchase
   * @returns Promise<{ sessionId: string; url: string }> - Stripe checkout session info
   */
  async buyCredits(
    args: Partial<{
      packageId: string;
    }>,
  ): Promise<{ sessionId: string; url: string; publishableKey: string }> {
    console.log("buyCredits: ", args);
    const packageId = ensure(args.packageId, "Missing packageId argument");

    const {
      data: { session },
    } = await this.supabaseClient.auth.getSession();
    if (!session) {
      throw new AuthError("No active session");
    }

    const response = await fetch("/api/v1/stripe/checkout", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${session.access_token}`,
      },
      body: JSON.stringify({ packageId }),
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
