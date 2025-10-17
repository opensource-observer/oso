import { NextRequest, NextResponse } from "next/server";
import { z } from "zod";
import { getUser } from "@/lib/auth/auth";
import { createBucketWithLifecycle } from "@/lib/clients/cloudflare-r2";
import { withPostHogTracking } from "@/lib/clients/posthog";
import { logger } from "@/lib/logger";

export const revalidate = 0;

const createBucketRequestSchema = z.object({
  orgName: z.string().min(1, "Organization name is required"),
});

type CreateBucketRequest = z.infer<typeof createBucketRequestSchema>;

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
      { error: "Admin privileges required to create R2 buckets" },
      { status: 403 },
    );
  }

  const body = await request.json();
  const validation = createBucketRequestSchema.safeParse(body);

  if (!validation.success) {
    return NextResponse.json(
      { error: validation.error.issues[0].message },
      { status: 400 },
    );
  }

  const { orgName }: CreateBucketRequest = validation.data;

  try {
    await createBucketWithLifecycle(orgName);
    logger.log(`Created R2 bucket for organization: ${orgName}`);

    return NextResponse.json({
      success: true,
      message: `R2 bucket created for ${orgName}`,
    });
  } catch (error) {
    logger.error(`Failed to create R2 bucket for ${orgName}:`, error);

    return NextResponse.json(
      {
        success: false,
        error: error instanceof Error ? error.message : "Unknown error",
      },
      { status: 500 },
    );
  }
});
