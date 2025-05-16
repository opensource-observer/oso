import { SupabaseClient } from "@supabase/supabase-js";
import { supabaseClient as defaultClient } from "./supabase";
import { Database, Tables } from "../types/supabase";
import { MissingDataError, AuthError } from "../types/errors";

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

  async getMyUserProfile() {
    const {
      data: { user },
      error: authError,
    } = await this.supabaseClient.auth.getUser();
    if (authError) {
      throw authError;
    } else if (!user) {
      throw new AuthError("Not logged in");
    }
    const { data, error } = await this.supabaseClient
      .from("user_profiles")
      .select("*")
      .eq("id", user.id)
      .single();
    if (error) {
      throw error;
    } else if (!data) {
      throw new MissingDataError("User profile not found");
    }
    return data;
  }

  async updateMyUserProfile(profile: Partial<Tables<"user_profiles">>) {
    const {
      data: { user },
      error: authError,
    } = await this.supabaseClient.auth.getUser();
    if (authError) {
      throw authError;
    } else if (!user) {
      throw new AuthError("Not logged in");
    }
    const { error } = await this.supabaseClient
      .from("user_profiles")
      .update({ ...profile, id: user.id })
      .eq("id", user.id);
    if (error) {
      throw error;
    }
  }

  async createApiKey(keyData: Pick<Tables<"api_keys">, "name" | "api_key">) {
    const {
      data: { user },
      error: authError,
    } = await this.supabaseClient.auth.getUser();
    if (authError) {
      throw authError;
    } else if (!user) {
      throw new AuthError("Not logged in");
    }
    const { error } = await this.supabaseClient
      .from("api_keys")
      .insert({ ...keyData, user_id: user.id });
    if (error) {
      throw error;
    }
  }

  async createOrganization() {}

  async getOrganization() {}

  async inviteUserToOrganization() {}

  async changeUserRole() {}

  async removeUserFromOrganization() {}

  async deleteOrganization() {}
}

export { OsoAppClient };
