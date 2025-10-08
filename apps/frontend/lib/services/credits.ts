import { createAdminClient } from "@/lib/supabase/admin";
import { logger } from "@/lib/logger";
import type { AnonUser, OrgUser, User } from "@/lib/types/user";
import { DOMAIN } from "@/lib/config";
import { PostHogTracker } from "@/lib/analytics/track";
import { EVENTS } from "@/lib/types/posthog";
import type {
  OrganizationCreditTransactionsRow as OrganizationCreditTransaction,
  OrganizationCreditsRow as OrganizationCredits,
} from "@/lib/types/schema-types";

type SupabaseClient = Awaited<ReturnType<typeof createAdminClient>>;

export const PLAN_NAMES = ["FREE", "STARTER", "PRO", "ENTERPRISE"] as const;
export type PlanName = (typeof PLAN_NAMES)[number];

export enum TransactionType {
  SQL_QUERY = "sql_query",
  GRAPHQL_QUERY = "graphql_query",
  CHAT_QUERY = "chat_query",
  TEXT2SQL = "text2sql",
  ADMIN_GRANT = "admin_grant",
  PURCHASE = "purchase",
  AGENT_QUERY = "agent_query",
  REFILL = "refill",
}

export interface OrganizationPlan {
  org_id: string;
  org_name: string;
  plan_name: string;
  price_per_credit: number;
}

export interface CreditErrorContext {
  orgName: string;
  planName: string;
  creditsBalance: number;
  nextRefillDate?: string | null;
  supportUrl?: string;
  billingContactEmail?: string;
}

export class InsufficientCreditsError extends Error {
  public readonly billingUrl: string;
  public readonly context: CreditErrorContext;

  constructor(context: CreditErrorContext, customMessage?: string) {
    const PROTOCOL = DOMAIN.includes("localhost") ? "http" : "https";
    const billingUrl = `${PROTOCOL}://${DOMAIN}/${context.orgName}/settings/billing`;

    let message = customMessage;
    if (!message) {
      const isEnterprise = context.planName === "ENTERPRISE";
      const isFree = context.planName === "FREE";

      if (isEnterprise) {
        const supportInfo = context.supportUrl
          ? `Contact your support team at ${context.supportUrl}`
          : context.billingContactEmail
            ? `Contact billing at ${context.billingContactEmail}`
            : "Contact your account manager";

        message = `Insufficient credits (${context.creditsBalance} remaining). ${supportInfo} or visit ${billingUrl} to add more credits.`;
      } else if (isFree) {
        const refillInfo = context.nextRefillDate
          ? ` Your next credit refill is ${new Date(context.nextRefillDate).toLocaleDateString()}.`
          : "";

        message = `Insufficient credits (${context.creditsBalance} remaining).${refillInfo} Contact sales at ${billingUrl} to upgrade your plan.`;
      } else {
        message = `Insufficient credits (${context.creditsBalance} remaining). Visit ${billingUrl} to add more credits.`;
      }
    }

    super(message);
    this.name = "InsufficientCreditsError";
    this.billingUrl = billingUrl;
    this.context = context;
  }

  static createWithContext(
    context: CreditErrorContext,
  ): InsufficientCreditsError {
    return new InsufficientCreditsError(context);
  }
}

interface TransactionLogParams {
  orgId: string;
  userId: string;
  amount: number;
  transactionType: TransactionType;
  apiEndpoint?: string;
  metadata?: Record<string, any>;
  error?: {
    type: "insufficient_credits" | "transaction_failed";
    details?: Record<string, any>;
  };
}

export class CreditsService {
  static isAnonymousUser(user: OrgUser | User): user is AnonUser {
    return user.role === "anonymous";
  }

  private static async logTransaction(
    client: SupabaseClient,
    params: TransactionLogParams,
  ): Promise<void> {
    const {
      orgId,
      userId,
      amount,
      transactionType,
      apiEndpoint,
      metadata,
      error,
    } = params;

    const finalMetadata = error
      ? { error: error.type, ...error.details, ...metadata }
      : metadata;

    await client.from("organization_credit_transactions").insert({
      org_id: orgId,
      user_id: userId,
      amount,
      transaction_type: transactionType,
      api_endpoint: apiEndpoint,
      metadata: finalMetadata,
      created_at: new Date().toISOString(),
    });
  }

  private static async validateUserAccess(
    client: SupabaseClient,
    actingUserId: string,
    orgId: string,
  ): Promise<void> {
    const { data: userAccess, error: accessError } = await client
      .from("users_by_organization")
      .select("user_id")
      .eq("user_id", actingUserId)
      .eq("org_id", orgId)
      .is("deleted_at", null)
      .single();

    if (accessError) {
      logger.error(`Database error while validating acting user access:`, {
        actingUserId,
        orgId,
        error: accessError,
      });
      throw new Error("Failed to validate user access to organization");
    }

    if (!userAccess) {
      logger.error(
        `Access denied: Acting user is not a member of organization:`,
        {
          actingUserId,
          orgId,
        },
      );
      throw new Error("Acting user does not have access to organization");
    }
  }

  private static async deductCreditsFromBalance(
    client: SupabaseClient,
    orgId: string,
    amount: number,
  ): Promise<{
    success: boolean;
    currentBalance: number;
    newBalance?: number;
  }> {
    const { data: creditsData, error: creditsError } = await client
      .from("organization_credits")
      .select("credits_balance")
      .eq("org_id", orgId)
      .single();

    if (creditsError) {
      logger.error("Error fetching organization credits:", creditsError);
      throw creditsError;
    }

    const currentBalance = creditsData.credits_balance || 0;

    if (currentBalance < amount) {
      return { success: false, currentBalance };
    }

    const newBalance = currentBalance - amount;
    const { error: updateError } = await client
      .from("organization_credits")
      .update({
        credits_balance: newBalance,
        updated_at: new Date().toISOString(),
      })
      .eq("org_id", orgId);

    if (updateError) {
      logger.error("Error updating organization credits:", updateError);
      throw updateError;
    }

    return { success: true, currentBalance, newBalance };
  }

  private static async handleInsufficientCredits(
    client: SupabaseClient,
    orgId: string,
    tracker: PostHogTracker,
    transactionType: TransactionType,
  ): Promise<never> {
    tracker.track(EVENTS.INSUFFICIENT_CREDITS, {
      type: transactionType,
    });

    const { data: orgData } = await client
      .from("organizations")
      .select(
        `
        org_name,
        enterprise_support_url,
        billing_contact_email,
        pricing_plan!inner(plan_name, refill_cycle_days),
        organization_credits(credits_balance, last_refill_at)
      `,
      )
      .eq("id", orgId)
      .single();

    if (orgData) {
      const credits = orgData.organization_credits;
      const plan = orgData.pricing_plan;

      const nextRefillDate =
        credits?.last_refill_at && plan?.refill_cycle_days
          ? new Date(
              new Date(credits.last_refill_at).getTime() +
                plan.refill_cycle_days * 24 * 60 * 60 * 1000,
            ).toISOString()
          : null;

      const errorContext: CreditErrorContext = {
        orgName: orgData.org_name,
        planName: plan?.plan_name || "UNKNOWN",
        creditsBalance: credits?.credits_balance || 0,
        nextRefillDate,
        supportUrl: orgData.enterprise_support_url || undefined,
        billingContactEmail: orgData.billing_contact_email || undefined,
      };

      throw InsufficientCreditsError.createWithContext(errorContext);
    }

    throw InsufficientCreditsError.createWithContext({
      orgName: "unknown",
      planName: "UNKNOWN",
      creditsBalance: 0,
    });
  }

  private static async getOrganizationRefillData(
    client: SupabaseClient,
    orgId: string,
  ): Promise<{
    currentBalance: number;
    maxCredits: number | null;
    refillCycleDays: number | null;
    lastRefillAt: string | null;
  }> {
    const { data: orgData, error: fetchError } = await client
      .from("organizations")
      .select(
        `
        pricing_plan!inner(
          max_credits_per_cycle,
          refill_cycle_days
        ),
        organization_credits!inner(
          credits_balance,
          last_refill_at
        )
      `,
      )
      .eq("id", orgId)
      .single();

    if (fetchError || !orgData) {
      logger.error("Error fetching organization data for refill:", fetchError);
      const credits = await CreditsService.getOrganizationCredits(orgId);
      return {
        currentBalance: credits?.credits_balance || 0,
        maxCredits: null,
        refillCycleDays: null,
        lastRefillAt: null,
      };
    }

    const planConfig = orgData.pricing_plan;
    const credits = orgData.organization_credits;

    return {
      currentBalance: credits.credits_balance,
      maxCredits: planConfig.max_credits_per_cycle,
      refillCycleDays: planConfig.refill_cycle_days,
      lastRefillAt: credits.last_refill_at,
    };
  }

  private static calculateRefillAmount(
    currentBalance: number,
    maxCredits: number | null,
    refillCycleDays: number | null,
    lastRefillAt: string | null,
  ): number {
    if (!maxCredits || !refillCycleDays || !lastRefillAt) {
      return 0;
    }

    const lastRefillDate = new Date(lastRefillAt);
    const now = new Date();
    const daysSinceRefill =
      (now.getTime() - lastRefillDate.getTime()) / (1000 * 60 * 60 * 24);

    const isRefillDue = daysSinceRefill >= refillCycleDays;
    const needsRefill = currentBalance < maxCredits;

    return isRefillDue && needsRefill ? maxCredits - currentBalance : 0;
  }

  private static async executeRefill(
    client: SupabaseClient,
    orgId: string,
    userId: string,
    currentBalance: number,
    refillAmount: number,
  ): Promise<number> {
    const newBalance = currentBalance + refillAmount;
    const now = new Date();

    await client
      .from("organization_credits")
      .update({
        credits_balance: newBalance,
        last_refill_at: now.toISOString(),
        updated_at: now.toISOString(),
      })
      .eq("org_id", orgId)
      .throwOnError();

    await client
      .from("organization_credit_transactions")
      .insert({
        org_id: orgId,
        user_id: userId,
        amount: refillAmount,
        transaction_type: TransactionType.REFILL,
        metadata: {
          reason: "monthly_credit_refill",
          previous_balance: currentBalance,
          new_balance: newBalance,
        },
        created_at: now.toISOString(),
      })
      .throwOnError();

    logger.log(
      `Refilled ${refillAmount} credits for org ${orgId}. New balance: ${newBalance}`,
    );
    return newBalance;
  }

  static async getOrganizationCredits(
    orgId: string,
  ): Promise<OrganizationCredits | null> {
    const supabaseClient = createAdminClient();
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
    const supabaseClient = createAdminClient();
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

  static async getOrganizationPlan(
    orgId: string,
  ): Promise<OrganizationPlan | null> {
    const supabaseClient = createAdminClient();
    const { data, error } = await supabaseClient
      .from("organizations")
      .select(
        `
        id,
        org_name,
        pricing_plan!inner(
          plan_name,
          price_per_credit
        )
      `,
      )
      .eq("id", orgId)
      .single();

    if (error) {
      logger.error("Error fetching organization plan:", error);
      return null;
    }

    if (!data?.pricing_plan) {
      logger.error("Organization plan data is missing");
      return null;
    }

    return {
      org_id: data.id,
      org_name: data.org_name,
      plan_name: data.pricing_plan.plan_name,
      price_per_credit: data.pricing_plan.price_per_credit,
    };
  }

  static async checkAndDeductOrganizationCredits(
    user: OrgUser | User,
    orgId: string,
    transactionType: TransactionType,
    tracker: PostHogTracker,
    apiEndpoint?: string,
    metadata?: Record<string, any>,
  ): Promise<OrganizationPlan | null> {
    if (CreditsService.isAnonymousUser(user)) {
      return null;
    }

    const client = createAdminClient();

    await CreditsService.validateUserAccess(client, user.userId, orgId);

    const credits = await CreditsService.checkAndRefillCredits(
      orgId,
      user.userId,
    );
    logger.log(`Post-refill credits balance for org ${orgId}: ${credits}`);

    const orgPlan = await CreditsService.getOrganizationPlan(orgId);
    const costPerCall = orgPlan?.price_per_credit || 1;

    try {
      const deductionResult = await CreditsService.deductCreditsFromBalance(
        client,
        orgId,
        costPerCall,
      );

      if (!deductionResult.success) {
        await CreditsService.logTransaction(client, {
          orgId,
          userId: user.userId,
          amount: -costPerCall,
          transactionType,
          apiEndpoint,
          metadata,
          error: {
            type: "insufficient_credits",
            details: {
              attempted_amount: costPerCall,
              current_balance: deductionResult.currentBalance,
            },
          },
        });

        await CreditsService.handleInsufficientCredits(
          client,
          orgId,
          tracker,
          transactionType,
        );
      }

      await CreditsService.logTransaction(client, {
        orgId,
        userId: user.userId,
        amount: -costPerCall,
        transactionType,
        apiEndpoint,
        metadata,
      });

      return orgPlan;
    } catch (error) {
      await CreditsService.logTransaction(client, {
        orgId,
        userId: user.userId,
        amount: -costPerCall,
        transactionType,
        apiEndpoint,
        metadata,
        error: {
          type: "transaction_failed",
          details: {
            sql_error: error instanceof Error ? error.message : String(error),
          },
        },
      });

      logger.error("Exception in checkAndDeductOrganizationCredits:", error);
      throw error;
    }
  }

  private static async checkAndRefillCredits(
    orgId: string,
    userId: string,
  ): Promise<number> {
    const client = createAdminClient();

    try {
      const refillData = await CreditsService.getOrganizationRefillData(
        client,
        orgId,
      );

      const refillAmount = CreditsService.calculateRefillAmount(
        refillData.currentBalance,
        refillData.maxCredits,
        refillData.refillCycleDays,
        refillData.lastRefillAt,
      );

      if (refillAmount > 0) {
        return await CreditsService.executeRefill(
          client,
          orgId,
          userId,
          refillData.currentBalance,
          refillAmount,
        );
      }

      return refillData.currentBalance;
    } catch (error) {
      logger.error("Exception in checkAndRefillCredits:", error);
      const credits = await CreditsService.getOrganizationCredits(orgId);
      return credits?.credits_balance || 0;
    }
  }
}
