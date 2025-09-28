import { getUser, signOsoJwt } from "@/lib/auth/auth";
import { withPostHogTracking } from "@/lib/clients/posthog";
import { logger } from "@/lib/logger";
import { createServerClient } from "@/lib/supabase/server";
import { NextRequest, NextResponse } from "next/server";

export const dynamic = "force-dynamic";

const JWT_EXPIRATION = "1w";

export const GET = withPostHogTracking(async (req: NextRequest) => {
  const orgName = req.nextUrl.searchParams.get("orgName");
  if (!orgName) {
    return NextResponse.json({ error: "Missing orgName" }, { status: 400 });
  }

  const user = await getUser(req);
  if (user.role === "anonymous") {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }
  const supabaseClient = await createServerClient();
  const { data, error } = await supabaseClient
    .from("organizations")
    .select("id")
    .eq("org_name", orgName)
    .single();

  if (error) {
    logger.error("Error fetching organization:", error);
    return NextResponse.json(
      {
        error: `Error fetching organization ${orgName}`,
      },
      { status: 500 },
    );
  }

  const jwt = await signOsoJwt(
    user,
    {
      orgId: data.id,
      orgName: orgName,
    },
    JWT_EXPIRATION,
  );

  return NextResponse.json({ token: jwt });
});
