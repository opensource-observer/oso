import { createServerClient } from "@/lib/supabase/server";
import { NextRequest, NextResponse } from "next/server";
import { sendInvitationEmail } from "@/lib/services/email";
import { logger } from "@/lib/logger";
import { z } from "zod";
import { v4 as uuid4 } from "uuid";

const CreateInvitationSchema = z.object({
  email: z.string().email("Invalid email address"),
  orgName: z.string().min(1, "Organization name is required"),
});

export async function POST(request: NextRequest) {
  try {
    const supabase = await createServerClient();
    const {
      data: { user },
    } = await supabase.auth.getUser();

    if (!user) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const { email, orgName } = CreateInvitationSchema.parse(
      await request.json(),
    );
    const normalizedEmail = email.toLowerCase().trim();

    const { data: userProfile } = await supabase
      .from("user_profiles")
      .select("*")
      .eq("id", user.id)
      .single();

    if (!userProfile) {
      return NextResponse.json(
        { error: "User profile not found" },
        {
          status: 404,
        },
      );
    }

    const { data: org, error: orgError } = await supabase
      .from("organizations")
      .select("*")
      .eq("org_name", orgName)
      .single();

    if (orgError || !org) {
      return NextResponse.json(
        { error: "Organization not found" },
        {
          status: 404,
        },
      );
    }

    const { data: membership } = await supabase
      .from("users_by_organization")
      .select("*")
      .eq("user_id", user.id)
      .eq("org_id", org.id)
      .is("deleted_at", null)
      .single();

    if (!membership) {
      return NextResponse.json(
        {
          error: "Not authorized for this organization",
        },
        { status: 403 },
      );
    }

    if (user.email?.toLowerCase() === normalizedEmail) {
      return NextResponse.json(
        {
          error: "You cannot invite yourself to an organization",
        },
        { status: 400 },
      );
    }

    const { data: existingUser } = await supabase
      .from("user_profiles")
      .select("id")
      .ilike("email", normalizedEmail)
      .single();

    if (existingUser) {
      const { data: existingMembership } = await supabase
        .from("users_by_organization")
        .select("*")
        .eq("user_id", existingUser.id)
        .eq("org_id", org.id)
        .is("deleted_at", null)
        .single();

      if (existingMembership) {
        return NextResponse.json(
          {
            error: "This user is already a member of the organization",
          },
          { status: 400 },
        );
      }
    }

    const { data: existingInvitation } = await supabase
      .from("invitations")
      .select("id, status, expires_at")
      .eq("org_id", org.id)
      .ilike("email", normalizedEmail)
      .eq("status", "pending")
      .is("deleted_at", null)
      .single();

    if (existingInvitation) {
      if (new Date(existingInvitation.expires_at) > new Date()) {
        return NextResponse.json(
          {
            error: "An active invitation already exists for this email",
          },
          { status: 400 },
        );
      }

      await supabase
        .from("invitations")
        .update({ status: "expired", updated_at: new Date().toISOString() })
        .eq("id", existingInvitation.id);
    }

    const invitationId = uuid4();

    try {
      await sendInvitationEmail({
        to: normalizedEmail,
        orgName: org.org_name,
        inviteToken: invitationId,
        inviterName: userProfile.full_name || userProfile.email || "Someone",
      });
    } catch (emailError) {
      logger.error("Failed to send invitation email:", emailError);
      return NextResponse.json(
        {
          error: "Failed to send invitation email",
        },
        { status: 500 },
      );
    }

    const { data: invitation, error } = await supabase
      .from("invitations")
      .insert({
        id: invitationId,
        email: normalizedEmail,
        org_name: org.org_name,
        org_id: org.id,
        invited_by: userProfile.id,
        status: "pending",
      })
      .select()
      .single();

    if (error) {
      logger.error("Database error:", error);
      return NextResponse.json({ error: error.message }, { status: 500 });
    }

    return NextResponse.json({
      invitation,
      message: `Invitation sent to ${normalizedEmail}`,
    });
  } catch (error) {
    if (error instanceof z.ZodError) {
      return NextResponse.json(
        {
          error: "Validation error",
          details: error.errors,
        },
        { status: 400 },
      );
    }
    logger.error("API error:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      {
        status: 500,
      },
    );
  }
}
