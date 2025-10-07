import { createServerClient } from "@/lib/supabase/server";
import { logger } from "@/lib/logger";
import type { AnonUser, OrgUser, User } from "@/lib/types/user";
import type { Json } from "@/lib/types/supabase";
import { DOMAIN } from "@/lib/config";
import { PostHogTracker } from "@/lib/analytics/track";
import { EVENTS } from "@/lib/types/posthog";

const CREDITS_PREVIEW_MODE = false;
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

export class CreditsService {
  static isAnonymousUser(user: OrgUser | User): user is AnonUser {
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

  static async getOrganizationPlan(
    orgId: string,
  ): Promise<OrganizationPlan | null> {
    const supabaseClient = await createServerClient();
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

    const orgPlan = await CreditsService.getOrganizationPlan(orgId);
    const costPerCall = orgPlan?.price_per_credit || 1;

    const supabaseClient = await createServerClient();
    const rpcFunction = CREDITS_PREVIEW_MODE
      ? "preview_deduct_organization_credits"
      : "deduct_organization_credits";

    const orgDataPromise = CREDITS_PREVIEW_MODE
      ? Promise.resolve(null)
      : supabaseClient
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

    const [{ data, error }, orgDataResult] = await Promise.all([
      supabaseClient.rpc(rpcFunction, {
        p_org_id: orgId,
        p_user_id: user.userId,
        p_amount: costPerCall,
        p_transaction_type: transactionType,
        p_api_endpoint: apiEndpoint,
        p_metadata: metadata,
      }),
      orgDataPromise,
    ]);

    if (CREDITS_PREVIEW_MODE) {
      logger.log(
        `Preview organization credit usage tracked for user ${user.userId} in org ${orgId} on ${transactionType} at ${apiEndpoint}`,
      );
      return orgPlan;
    }

    if (error || !data) {
      if (error) {
        logger.error("Error deducting organization credits:", error);
      }

      tracker.track(EVENTS.INSUFFICIENT_CREDITS, {
        type: transactionType,
      });

      if (orgDataResult?.data) {
        const orgData = orgDataResult.data;
        const credits = orgData.organization_credits;
        const plan = orgData.pricing_plan;

        let nextRefillDate: string | null = null;
        if (credits?.last_refill_at && plan?.refill_cycle_days) {
          const lastRefill = new Date(credits.last_refill_at);
          nextRefillDate = new Date(
            lastRefill.getTime() + plan.refill_cycle_days * 24 * 60 * 60 * 1000,
          ).toISOString();
        }

        const errorContext: CreditErrorContext = {
          orgName: orgData.org_name,
          planName: plan?.plan_name || "UNKNOWN",
          creditsBalance: credits?.credits_balance || 0,
          nextRefillDate,
          supportUrl: orgData.enterprise_support_url || undefined,
          billingContactEmail: orgData.billing_contact_email || undefined,
        };

        throw InsufficientCreditsError.createWithContext(errorContext);
      } else {
        throw InsufficientCreditsError.createWithContext({
          orgName: "unknown",
          planName: "UNKNOWN",
          creditsBalance: 0,
        });
      }
    }

    return orgPlan;
  }
}
