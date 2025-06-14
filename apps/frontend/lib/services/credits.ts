import { createServerClient } from "@/lib/supabase/server";
import { logger } from "@/lib/logger";
import type { AnonUser, User } from "@/lib/types/user";
import type { Json } from "@/lib/types/supabase";

// TODO(jabolo): Disable this once we transition to the new credits system
const CREDITS_PREVIEW_MODE = true;

export enum TransactionType {
  SQL_QUERY = "sql_query",
  GRAPHQL_QUERY = "graphql_query",
  CHAT_QUERY = "chat_query",
  ADMIN_GRANT = "admin_grant",
  PURCHASE = "purchase",
}

export interface CreditTransaction {
  id: string;
  user_id: string;
  amount: number;
  transaction_type: string;
  api_endpoint?: string | null;
  created_at: string;
  metadata?: Json | null;
}

export interface OrganizationCreditTransaction {
  id: string;
  org_id: string;
  user_id: string;
  amount: number;
  transaction_type: string;
  api_endpoint?: string | null;
  created_at: string;
  metadata?: Json | null;
}

export interface UserCredits {
  id: string;
  user_id: string;
  credits_balance: number;
  created_at: string;
  updated_at: string;
}

export interface OrganizationCredits {
  id: string;
  org_id: string;
  credits_balance: number;
  created_at: string;
  updated_at: string;
}

const COST_PER_API_CALL = 1;

export class CreditsService {
  static isAnonymousUser(user: User): user is AnonUser {
    return user.role === "anonymous";
  }

  static async getUserCredits(userId: string): Promise<UserCredits | null> {
    const supabaseClient = await createServerClient();
    const { data, error } = await supabaseClient
      .from("user_credits")
      .select("*")
      .eq("user_id", userId)
      .single();

    if (error) {
      logger.error("Error fetching user credits:", error);
      return null;
    }

    return data;
  }

  static async getOrganizationCredits(
    orgId: string,
  ): Promise<OrganizationCredits | null> {
    const { data, error } = await supabaseClient
      .from("organization_credits")
      .select("*")
      .eq("org_id", orgId)
      .single();

    if (error) {
      logger.error("Error fetching organization credits:", error);
      return null;
    }

    return data;
  }

  static async getCreditTransactions(
    userId: string,
    limit = 50,
    offset = 0,
  ): Promise<CreditTransaction[]> {
    const supabaseClient = await createServerClient();
    const { data, error } = await supabaseClient
      .from("credit_transactions")
      .select("*")
      .eq("user_id", userId)
      .order("created_at", { ascending: false })
      .range(offset, offset + limit - 1);

    if (error) {
      logger.error("Error fetching credit transactions:", error);
      return [];
    }

    return data || [];
  }

  static async getOrganizationCreditTransactions(
    orgId: string,
    limit = 50,
    offset = 0,
  ): Promise<OrganizationCreditTransaction[]> {
    const { data, error } = await supabaseClient
      .from("organization_credit_transactions")
      .select("*")
      .eq("org_id", orgId)
      .order("created_at", { ascending: false })
      .range(offset, offset + limit - 1);

    if (error) {
      logger.error("Error fetching organization credit transactions:", error);
      return [];
    }

    return data || [];
  }

  static async checkAndDeductCredits(
    user: User,
    transactionType: TransactionType,
    apiEndpoint?: string,
    metadata?: Record<string, any>,
  ): Promise<boolean> {
    if (CreditsService.isAnonymousUser(user)) {
      return CREDITS_PREVIEW_MODE;
    }

    const rpcFunction = CREDITS_PREVIEW_MODE
      ? "preview_deduct_credits"
      : "deduct_credits";

    const supabaseClient = await createServerClient();
    const { data, error } = await supabaseClient.rpc(rpcFunction, {
      p_user_id: user.userId,
      p_amount: COST_PER_API_CALL,
      p_transaction_type: transactionType,
      p_api_endpoint: apiEndpoint,
      p_metadata: metadata,
    });

    if (error) {
      logger.error(
        `Error ${CREDITS_PREVIEW_MODE ? "previewing" : "deducting"} credits:`,
        error,
      );
      return false;
    }

    if (CREDITS_PREVIEW_MODE) {
      logger.log(
        `Preview credit usage tracked for user ${user.userId} on ${transactionType} at ${apiEndpoint}`,
      );
    }

    return data;
  }

  static async checkAndDeductOrganizationCredits(
    user: User,
    orgId: string,
    transactionType: TransactionType,
    apiEndpoint?: string,
    metadata?: Record<string, any>,
  ): Promise<boolean> {
    if (CreditsService.isAnonymousUser(user)) {
      return CREDITS_PREVIEW_MODE;
    }

    const rpcFunction = CREDITS_PREVIEW_MODE
      ? "preview_deduct_organization_credits"
      : "deduct_organization_credits";

    const { data, error } = await supabaseClient.rpc(rpcFunction, {
      p_org_id: orgId,
      p_user_id: user.userId,
      p_amount: COST_PER_API_CALL,
      p_transaction_type: transactionType,
      p_api_endpoint: apiEndpoint,
      p_metadata: metadata,
    });

    if (error) {
      logger.error(
        `Error ${CREDITS_PREVIEW_MODE ? "previewing" : "deducting"} organization credits:`,
        error,
      );
      return false;
    }

    if (CREDITS_PREVIEW_MODE) {
      logger.log(
        `Preview organization credit usage tracked for user ${user.userId} in org ${orgId} on ${transactionType} at ${apiEndpoint}`,
      );
    }

    return data;
  }

  static async getUserPrimaryOrganization(
    userId: string,
  ): Promise<string | null> {
    const { data, error } = await supabaseClient
      .from("users_by_organization")
      .select("org_id")
      .eq("user_id", userId)
      .is("deleted_at", null)
      .order("created_at", { ascending: true })
      .limit(1)
      .single();

    if (error) {
      logger.error("Error fetching user primary organization:", error);
      return null;
    }

    return data?.org_id || null;
  }

  static async checkAndDeductCreditsWithOrgFallback(
    user: User,
    transactionType: TransactionType,
    apiEndpoint?: string,
    metadata?: Record<string, any>,
  ): Promise<boolean> {
    if (CreditsService.isAnonymousUser(user)) {
      return CREDITS_PREVIEW_MODE;
    }

    const orgId = await CreditsService.getUserPrimaryOrganization(user.userId);
    if (orgId) {
      return CreditsService.checkAndDeductOrganizationCredits(
        user,
        orgId,
        transactionType,
        apiEndpoint,
        metadata,
      );
    }

    return CreditsService.checkAndDeductCredits(
      user,
      transactionType,
      apiEndpoint,
      metadata,
    );
  }
}
