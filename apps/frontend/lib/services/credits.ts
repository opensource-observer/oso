import { createServerClient } from "@/lib/supabase/server";
import { logger } from "@/lib/logger";
import type { AnonUser, User } from "@/lib/types/user";
import type { Json } from "@/lib/types/supabase";
import { DOMAIN } from "@/lib/config";

// TODO(jabolo): Disable this once we transition to the new credits system
const CREDITS_PREVIEW_MODE = true;

export enum TransactionType {
  SQL_QUERY = "sql_query",
  GRAPHQL_QUERY = "graphql_query",
  CHAT_QUERY = "chat_query",
  TEXT2SQL = "text2sql",
  ADMIN_GRANT = "admin_grant",
  PURCHASE = "purchase",
  AGENT_QUERY = "agent_query",
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

export interface OrganizationCredits {
  id: string;
  org_id: string;
  credits_balance: number;
  created_at: string;
  updated_at: string;
}

const COST_PER_API_CALL = 1;

export class InsufficientCreditsError extends Error {
  constructor(
    public orgName: string,
    public billingUrl: string,
    message?: string,
  ) {
    const defaultMessage = `Insufficient credits to complete this request. Please add more credits at ${billingUrl}`;
    super(message || defaultMessage);
    this.name = "InsufficientCreditsError";
  }

  static create(orgName: string): InsufficientCreditsError {
    const PROTOCOL = DOMAIN.includes("localhost") ? "http" : "https";
    const billingUrl = `${PROTOCOL}://${DOMAIN}/${orgName}/settings/billing`;
    return new InsufficientCreditsError(orgName, billingUrl);
  }
}

export class CreditsService {
  static isAnonymousUser(user: User): user is AnonUser {
    return user.role === "anonymous";
  }

  static async getOrganizationCredits(
    orgId: string,
  ): Promise<OrganizationCredits | null> {
    const supabaseClient = await createServerClient();
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

  static async getOrganizationCreditTransactions(
    orgId: string,
    limit = 50,
    offset = 0,
  ): Promise<OrganizationCreditTransaction[]> {
    const supabaseClient = await createServerClient();
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

    const supabaseClient = await createServerClient();
    const rpcFunction = CREDITS_PREVIEW_MODE
      ? "preview_deduct_organization_credits"
      : "deduct_organization_credits";

    const orgNamePromise = CREDITS_PREVIEW_MODE
      ? Promise.resolve(null)
      : supabaseClient
          .from("organizations")
          .select("org_name")
          .eq("id", orgId)
          .single();

    const [{ data, error }, orgResult] = await Promise.all([
      supabaseClient.rpc(rpcFunction, {
        p_org_id: orgId,
        p_user_id: user.userId,
        p_amount: COST_PER_API_CALL,
        p_transaction_type: transactionType,
        p_api_endpoint: apiEndpoint,
        p_metadata: metadata,
      }),
      orgNamePromise,
    ]);

    if (CREDITS_PREVIEW_MODE) {
      logger.log(
        `Preview organization credit usage tracked for user ${user.userId} in org ${orgId} on ${transactionType} at ${apiEndpoint}`,
      );
      return true;
    }

    if (error || !data) {
      if (error) {
        logger.error("Error deducting organization credits:", error);
      }
      const orgName = orgResult?.data?.org_name || "unknown";
      throw InsufficientCreditsError.create(orgName);
    }

    return data;
  }
}
