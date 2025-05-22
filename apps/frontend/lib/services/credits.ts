import { createNormalSupabaseClient } from "../clients/supabase";
import { logger } from "../logger";
import type { AnonUser, User } from "../types/user";
import type { Json } from "../types/supabase";

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

export interface UserCredits {
  id: string;
  user_id: string;
  credits_balance: number;
  created_at: string;
  updated_at: string;
}

const COST_PER_API_CALL = 1;

const supabaseClient = createNormalSupabaseClient();

export class CreditsService {
  static isAnonymousUser(user: User): user is AnonUser {
    return user.role === "anonymous";
  }

  static async getUserCredits(userId: string): Promise<UserCredits | null> {
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

  static async getCreditTransactions(
    userId: string,
    limit = 50,
    offset = 0,
  ): Promise<CreditTransaction[]> {
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

  static async checkAndDeductCredits(
    user: User,
    transactionType: TransactionType,
    apiEndpoint?: string,
    metadata?: Record<string, any>,
  ): Promise<boolean> {
    if (CreditsService.isAnonymousUser(user)) {
      return false;
    }

    const rpcFunction = CREDITS_PREVIEW_MODE
      ? "preview_deduct_credits"
      : "deduct_credits";

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
}
