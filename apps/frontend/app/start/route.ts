import { NextRequest, NextResponse } from "next/server";
import _ from "lodash";
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

  // Check if the user is part of any any organizations
  const { data: joinedOrgs, error: joinError } = await supabaseClient
    .from("users_by_organization")
    .select(
      "*, organizations!inner(id, org_name, created_at, pricing_plan!inner(price_per_credit))",
    )
    .eq("user_id", user.userId)
    .is("deleted_at", null);

  if (joinError) {
    throw joinError;
  } else if (!joinedOrgs || joinedOrgs.length <= 0) {
    // We proxy instead of redirect to keep us on /start
    return NextResponse.rewrite(new URL("/create-org", req.url));
  }

  // Find the user's highest tier organization
  // TODO: this is a hack to find the highest tier plan
  const flattened = joinedOrgs.map((x) => ({
    id: x.organizations.id,
    org_name: x.organizations.org_name,
    price_per_credit: x.organizations.pricing_plan.price_per_credit,
    created_at: x.organizations.created_at,
  }));
  const sorted = _.sortBy(flattened, ["price_per_credit", "created_at"]);
  const org = sorted[0];

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
    // TODO: enable this once we have wired up public notebooks
    //return NextResponse.rewrite(new URL("/examples", req.url));
  }

  // Default logged-in case - redirect to organization dashboard
  return NextResponse.redirect(new URL(`/${org.org_name}`, req.url));
});
