import { NextRequest, NextResponse } from "next/server";
import { logger } from "@/lib/logger";
import { getUser } from "@/lib/auth/auth";
import { createServerClient } from "@/lib/supabase/server";
import { withPostHogTracking } from "@/lib/clients/posthog";

export const dynamic = "force-dynamic";

export const GET = withPostHogTracking(async (req: NextRequest) => {
  const supabaseClient = await createServerClient();
  const user = await getUser(req);

  // Check if user is anonymous
  if (user.role === "anonymous") {
    logger.log(`/start: User is anonymous`);
    return NextResponse.redirect(new URL("/login", req.url));
  }

  // Check if the user has created any organizations
  const { data: org, error: orgError } = await supabaseClient
    .from("organizations")
    .select("id,org_name,pricing_plan!inner(price_per_credit)")
    .eq("created_by", user.userId)
    .is("deleted_at", null)
    // TODO: this is a hack to find the highest tier plan
    .order("pricing_plan.price_per_credit", {
      ascending: true,
      nullsFirst: false,
    })
    .single();
  if (orgError) {
    throw orgError;
  } else if (!org) {
    // We proxy instead of redirect to keep us on /start
    return NextResponse.rewrite(new URL("/create-org", req.url));
  }

  // Look for any existing notebooks
  const { data: notebookData, error: notebookError } = await supabaseClient
    .from("notebooks")
    .select("*")
    .eq("org_id", org.id)
    .is("deleted_at", null);
  if (notebookError) {
    throw notebookError;
  } else if (!notebookData || notebookData.length <= 0) {
    // We proxy instead of redirect to keep us on /start
    return NextResponse.rewrite(new URL("/examples", req.url));
  }

  // Default logged-in case - redirect to organization dashboard
  return NextResponse.redirect(new URL(`/${org.org_name}`, req.url));
});
