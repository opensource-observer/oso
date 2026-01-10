import crypto from "crypto";
import { createClient } from "@supabase/supabase-js";
import { SUPABASE_SERVICE_KEY, SUPABASE_URL } from "@/lib/config";
import {
  CreditsService,
  InsufficientCreditsError,
  TransactionType,
} from "@/lib/services/credits";
import type { OrgUser } from "@/lib/types/user";
import { PostHogTracker } from "@/lib/analytics/track";
import type { Database } from "@/lib/types/supabase";

let testSupabaseClient: ReturnType<typeof createClient<Database>>;

jest.mock("@/lib/supabase/admin", () => ({
  createServerClient: jest.fn(() => testSupabaseClient),
  createAdminClient: jest.fn(() => testSupabaseClient),
}));

describe("CreditsService", () => {
  const TEST_ORG_ID = crypto.randomUUID();
  const TEST_USER_ID = crypto.randomUUID();
  const FREE_PLAN_COST = 1;

  let adminSupabase: ReturnType<typeof createClient<Database>>;
  let mockTracker: PostHogTracker;

  beforeAll(async () => {
    adminSupabase = createClient<Database>(SUPABASE_URL, SUPABASE_SERVICE_KEY, {
      auth: { storageKey: "credits-test-auth" },
    });
    testSupabaseClient = adminSupabase;

    mockTracker = { track: jest.fn() } as unknown as PostHogTracker;

    await adminSupabase
      .from("organization_credit_transactions")
      .delete()
      .eq("org_id", TEST_ORG_ID);
    await adminSupabase
      .from("organization_credits")
      .delete()
      .eq("org_id", TEST_ORG_ID);
    await adminSupabase
      .from("users_by_organization")
      .delete()
      .eq("org_id", TEST_ORG_ID);
    await adminSupabase.from("organizations").delete().eq("id", TEST_ORG_ID);
    await adminSupabase.from("user_profiles").delete().eq("id", TEST_USER_ID);
    await adminSupabase.auth.admin.deleteUser(TEST_USER_ID).catch(() => {});

    await adminSupabase.auth.admin.createUser({
      id: TEST_USER_ID,
      email: `credits_test_${TEST_USER_ID}@test.com`,
      password: "password123",
      email_confirm: true,
    });

    await adminSupabase
      .from("user_profiles")
      .upsert(
        {
          id: TEST_USER_ID,
          email: `credits_test_${TEST_USER_ID}@test.com`,
          full_name: "Credits Test User",
        },
        { onConflict: "id" },
      )
      .throwOnError();

    const { data: freePlan } = await adminSupabase
      .from("pricing_plan")
      .select("*")
      .eq("plan_name", "FREE")
      .single()
      .throwOnError();
    if (!freePlan) throw new Error("FREE plan not found");

    await adminSupabase
      .from("organizations")
      .upsert(
        {
          id: TEST_ORG_ID,
          created_by: TEST_USER_ID,
          org_name: `credits_test_${TEST_ORG_ID.substring(0, 8)}`,
          plan_id: freePlan.plan_id,
        },
        { onConflict: "id" },
      )
      .throwOnError();

    await adminSupabase
      .from("organization_credits")
      .upsert(
        {
          org_id: TEST_ORG_ID,
          credits_balance: 100,
          last_refill_at: new Date().toISOString(),
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
        { onConflict: "org_id" },
      )
      .throwOnError();

    const { data: verifyOrg } = await adminSupabase
      .from("organizations")
      .select(
        `
        id,
        org_name,
        pricing_plan!inner(plan_name, max_credits_per_cycle, refill_cycle_days),
        organization_credits!inner(credits_balance)
      `,
      )
      .eq("id", TEST_ORG_ID)
      .single()
      .throwOnError();

    if (!verifyOrg) {
      throw new Error("Failed to verify org setup: Org not found");
    }
  });

  afterAll(async () => {
    await adminSupabase
      .from("organization_credit_transactions")
      .delete()
      .eq("org_id", TEST_ORG_ID);
    await adminSupabase
      .from("organization_credits")
      .delete()
      .eq("org_id", TEST_ORG_ID);
    await adminSupabase
      .from("users_by_organization")
      .delete()
      .eq("org_id", TEST_ORG_ID);
    await adminSupabase.from("organizations").delete().eq("id", TEST_ORG_ID);
    await adminSupabase.from("user_profiles").delete().eq("id", TEST_USER_ID);
    await adminSupabase.auth.admin.deleteUser(TEST_USER_ID);
  });

  afterEach(async () => {
    await adminSupabase
      .from("organization_credits")
      .update({ credits_balance: 100, updated_at: new Date().toISOString() })
      .eq("org_id", TEST_ORG_ID);
  });

  describe("checkAndDeductOrganizationCredits", () => {
    it("should deduct credits successfully", async () => {
      const user: OrgUser = {
        userId: TEST_USER_ID,
        role: "user",
        orgId: TEST_ORG_ID,
        orgName: "test",
        orgRole: "admin",
        name: "Test User",
        keyName: "test-key",
        host: null,
      };

      const result = await CreditsService.checkAndDeductOrganizationCredits(
        user,
        TEST_ORG_ID,
        TransactionType.AGENT_QUERY,
        mockTracker,
      );

      expect(result).toBeDefined();
      expect(result?.plan_name).toBe("FREE");

      const { data: credits } = await adminSupabase
        .from("organization_credits")
        .select("credits_balance")
        .eq("org_id", TEST_ORG_ID)
        .single();

      expect(credits?.credits_balance).toBe(100 - FREE_PLAN_COST);
    });

    it("should throw InsufficientCreditsError when balance too low", async () => {
      await adminSupabase
        .from("organization_credits")
        .update({ credits_balance: 0 })
        .eq("org_id", TEST_ORG_ID);

      const user: OrgUser = {
        userId: TEST_USER_ID,
        role: "user",
        orgId: TEST_ORG_ID,
        orgName: "test",
        orgRole: "admin",
        name: "Test User",
        keyName: "test-key",
        host: null,
      };

      await expect(
        CreditsService.checkAndDeductOrganizationCredits(
          user,
          TEST_ORG_ID,
          TransactionType.AGENT_QUERY,
          mockTracker,
        ),
      ).rejects.toThrow(InsufficientCreditsError);

      expect(mockTracker.track).toHaveBeenCalled();
    });

    it("should return null for anonymous users", async () => {
      const anonUser: OrgUser = { role: "anonymous" as const, host: null };

      const result = await CreditsService.checkAndDeductOrganizationCredits(
        anonUser,
        TEST_ORG_ID,
        TransactionType.AGENT_QUERY,
        mockTracker,
      );

      expect(result).toBeNull();
    });
  });

  describe("credit refill", () => {
    it("should refill credits when cycle has elapsed", async () => {
      const oldRefillDate = new Date();
      oldRefillDate.setDate(oldRefillDate.getDate() - 31);

      await adminSupabase
        .from("organization_credits")
        .update({
          credits_balance: 50,
          last_refill_at: oldRefillDate.toISOString(),
        })
        .eq("org_id", TEST_ORG_ID);

      const user: OrgUser = {
        userId: TEST_USER_ID,
        role: "user",
        orgId: TEST_ORG_ID,
        orgName: "test",
        orgRole: "admin",
        name: "Test User",
        keyName: "test-key",
        host: null,
      };

      await CreditsService.checkAndDeductOrganizationCredits(
        user,
        TEST_ORG_ID,
        TransactionType.AGENT_QUERY,
        mockTracker,
      );

      const { data: credits } = await adminSupabase
        .from("organization_credits")
        .select("credits_balance")
        .eq("org_id", TEST_ORG_ID)
        .single();

      const { data: plan } = await adminSupabase
        .from("pricing_plan")
        .select("*")
        .eq("plan_name", "FREE")
        .single();

      const maxCredits = plan?.max_credits_per_cycle ?? 100;
      expect(credits?.credits_balance).toBe(maxCredits - FREE_PLAN_COST);

      const { data: transactions } = await adminSupabase
        .from("organization_credit_transactions")
        .select("*")
        .eq("org_id", TEST_ORG_ID)
        .eq("transaction_type", TransactionType.REFILL)
        .order("created_at", { ascending: false })
        .limit(1);

      expect(transactions).toHaveLength(1);
      expect(transactions?.[0]?.amount).toBeGreaterThan(0);
    });

    it("should not refill when cycle hasn't elapsed", async () => {
      const recentRefill = new Date();
      recentRefill.setDate(recentRefill.getDate() - 5);

      await adminSupabase
        .from("organization_credits")
        .update({
          credits_balance: 50,
          last_refill_at: recentRefill.toISOString(),
        })
        .eq("org_id", TEST_ORG_ID);

      const user: OrgUser = {
        userId: TEST_USER_ID,
        role: "user",
        orgId: TEST_ORG_ID,
        orgName: "test",
        orgRole: "admin",
        name: "Test User",
        keyName: "test-key",
        host: null,
      };

      await CreditsService.checkAndDeductOrganizationCredits(
        user,
        TEST_ORG_ID,
        TransactionType.AGENT_QUERY,
        mockTracker,
      );

      const { data: credits } = await adminSupabase
        .from("organization_credits")
        .select("credits_balance")
        .eq("org_id", TEST_ORG_ID)
        .single();

      expect(credits?.credits_balance).toBe(50 - FREE_PLAN_COST);
    });
  });

  describe("getOrganizationPlan", () => {
    it("should return plan details", async () => {
      const plan = await CreditsService.getOrganizationPlan(TEST_ORG_ID);

      expect(plan).toBeDefined();
      expect(plan?.plan_name).toBe("FREE");
      expect(plan?.org_id).toBe(TEST_ORG_ID);
    });

    it("should return null for non-existent org", async () => {
      const plan = await CreditsService.getOrganizationPlan(
        crypto.randomUUID(),
      );

      expect(plan).toBeNull();
    });
  });

  describe("getOrganizationCredits", () => {
    it("should return credits balance", async () => {
      const credits = await CreditsService.getOrganizationCredits(TEST_ORG_ID);

      expect(credits).toBeDefined();
      expect(credits?.credits_balance).toBe(100);
      expect(credits?.org_id).toBe(TEST_ORG_ID);
    });
  });
});
