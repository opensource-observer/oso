import { NextRequest, NextResponse } from "next/server";
import { logger } from "@/lib/logger";
import { getOrgUser } from "@/lib/auth/auth";
import { createServerClient } from "@/lib/supabase/server";
import { withPostHogTracking } from "@/lib/clients/posthog";

export const dynamic = "force-dynamic";

export const GET = withPostHogTracking(async (req: NextRequest) => {
  const supabaseClient = await createServerClient();
  const user = await getOrgUser(req);

  // Check if user is anonymous
  if (user.role === "anonymous") {
    logger.log(`/start: User is anonymous`);
    return NextResponse.redirect(new URL("/login", req.url));
  }

  // Check if the user has created any organizations
  const { data: createdOrgs, error: createdError } = await supabaseClient
    .from("organizations")
    .select("id")
    .eq("created_by", user.userId)
    .is("deleted_at", null);
  if (createdError) {
    throw createdError;
  } else if (!createdOrgs || createdOrgs.length <= 0) {
    // We proxy instead of redirect to keep us on /start
    return NextResponse.rewrite(new URL("/create-org", req.url));
  }

  // Look for any existing notebooks
  const orgName = user.orgName;
  const { data: notebookData, error: notebookError } = await supabaseClient
    .from("notebooks")
    .select("*,organizations!inner(org_name)")
    .eq("organizations.org_name", orgName)
    .is("deleted_at", null);
  if (notebookError) {
    throw notebookError;
  } else if (!notebookData || notebookData.length <= 0) {
    // We proxy instead of redirect to keep us on /start
    return NextResponse.rewrite(new URL("/examples", req.url));
  }

  // Default logged-in case - redirect to organization dashboard
  return NextResponse.redirect(new URL(`/${orgName}`, req.url));
});
