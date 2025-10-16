import { NextRequest, NextResponse } from "next/server";
import { z } from "zod";
import { createServerClient } from "@/lib/supabase/server";
import { getUser } from "@/lib/auth/auth";
import { createBucketWithLifecycle } from "@/lib/clients/cloudflare-r2";
import { withPostHogTracking } from "@/lib/clients/posthog";
import { logger } from "@/lib/logger";

export const revalidate = 0;

const promoteRequestSchema = z.object({
  orgName: z.string().min(1, "Organization name is required"),
});

export const POST = withPostHogTracking(async (request: NextRequest) => {
  const user = await getUser(request);

  if (user.role === "anonymous") {
    return NextResponse.json(
      { error: "Authentication required" },
      { status: 401 },
    );
  }

  if (user.role !== "admin") {
    return NextResponse.json(
      { error: "Admin privileges required to promote organizations" },
      { status: 403 },
    );
  }

  const body = await request.json();
  const validation = promoteRequestSchema.safeParse(body);

  if (!validation.success) {
    return NextResponse.json(
      { error: validation.error.issues[0].message },
      { status: 400 },
    );
  }

  const { orgName } = validation.data;

  const supabaseClient = await createServerClient();

  const { data: enterprisePlan, error: planError } = await supabaseClient
    .from("pricing_plan")
    .select("plan_id")
    .eq("plan_name", "ENTERPRISE")
    .order("updated_at", { ascending: false })
    .limit(1)
    .single();

  if (planError || !enterprisePlan) {
    return NextResponse.json(
      { error: "Enterprise plan not found" },
      { status: 500 },
    );
  }

  const { error: updateError } = await supabaseClient
    .from("organizations")
    .update({ plan_id: enterprisePlan.plan_id })
    .eq("org_name", orgName);

  if (updateError) {
    return NextResponse.json(
      { error: `Failed to promote organization: ${updateError.message}` },
      { status: 500 },
    );
  }

  try {
    await createBucketWithLifecycle(orgName);
    logger.log(`Created R2 bucket for enterprise org: ${orgName}`);

    return NextResponse.json({
      success: true,
      message: `Organization ${orgName} promoted to enterprise`,
      bucketCreated: true,
    });
  } catch (error) {
    logger.error(`Failed to create R2 bucket for ${orgName}:`, error);

    return NextResponse.json({
      success: true,
      message: `Organization ${orgName} promoted to enterprise`,
      bucketCreated: false,
      bucketError: error instanceof Error ? error.message : "Unknown error",
    });
  }
});
