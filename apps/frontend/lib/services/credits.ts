import { supabaseClient } from "../clients/supabase";
import { logger } from "../logger";
import { User } from "../types/user";

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
  api_endpoint?: string;
  created_at: string;
  metadata?: Record<string, any>;
}

export interface UserCredits {
  id: string;
  user_id: string;
  credits_balance: number;
  created_at: string;
  updated_at: string;
}

const COST_PER_API_CALL = 1;

export const CreditsService = {
  async getUserCredits(userId: string): Promise<UserCredits | null> {
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
  },

  async getCreditTransactions(
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
  },

  async checkAndDeductCredits(
    user: User,
    transactionType: TransactionType,
    apiEndpoint?: string,
    metadata?: Record<string, any>,
  ): Promise<boolean> {
    if (user.role === "anonymous") {
      return false;
    }

    const { data, error } = await supabaseClient.rpc("deduct_credits", {
      p_user_id: user.userId,
      p_amount: COST_PER_API_CALL,
      p_transaction_type: transactionType,
      p_api_endpoint: apiEndpoint,
      p_metadata: metadata,
    });

    if (error) {
      logger.error("Error deducting credits:", error);
      return false;
    }

    return data;
  },
};
