import { NextRequest, NextResponse } from "next/server";
import { logger } from "@/lib/logger";
import { getOrgUser } from "@/lib/auth/auth";
import { createServerClient } from "@/lib/supabase/server";
import { withPostHogTracking } from "@/lib/clients/posthog";

export const dynamic = "force-dynamic";

export const GET = withPostHogTracking(async (req: NextRequest) => {
  const supabaseClient = await createServerClient();
  const user = await getOrgUser(req);

  if (user.role === "anonymous") {
    logger.log(`/start: User is anonymous`);
    return NextResponse.redirect(new URL("/login", req.url));
  }
  const orgName = user.orgName;
  // Look for any existing notebooks
  const { data, error } = await supabaseClient
    .from("notebooks")
    .select("*,organizations!inner(org_name)")
    .eq("organizations.org_name", orgName)
    .is("deleted_at", null);
  if (error) {
    throw error;
  } else if (!data || data.length <= 0) {
    return NextResponse.redirect(new URL("/get-started", req.url));
  }
  return NextResponse.redirect(new URL(`/${orgName}`, req.url));
});
